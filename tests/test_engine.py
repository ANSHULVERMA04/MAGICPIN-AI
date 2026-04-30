"""
Unit tests for the scoring engine, renderer, and storage layer.
Run: pytest tests/
"""
import pytest
from app.engine.scorer import (
    score_context,
    _bookings_drop_pct,
    _is_peak_hour,
    _has_active_offer,
)
from app.engine.renderer import build_render_context, render_message, message_hash
from app.storage.store import ContextStore


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def fresh_store() -> ContextStore:
    """Reset singleton for test isolation."""
    ContextStore._instance = None
    return ContextStore.get_instance()


def seed_full_context(store: ContextStore, cid: str = "test-001"):
    store.upsert_context(cid, "merchant", 1, {
        "name": "SmileCare Dental",
        "category": "dentist",
        "city": "Bangalore",
        "locality": "Indiranagar",
        "metrics": {
            "bookings_this_week": 12,
            "bookings_last_week": 16,
            "avg_rating": 4.6,
            "repeat_customer_pct": 60,
        },
        "offers": [{"title": "₹299 Checkup", "fixed_price": 299, "active": True}],
        "last_message_sent_at": None,
    })
    store.upsert_context(cid, "trigger", 1, {
        "type": "search_spike",
        "search_count": 190,
        "search_keyword": "Dental Checkup",
        "hour_of_day": 19,
        "day_of_week": "Friday",
    })
    store.upsert_context(cid, "customer", 1, {
        "intent": "booking",
        "price_sensitive": True,
        "responsiveness": "high",
        "past_visits": 0,
    })


# ─────────────────────────────────────────────
# Utility function tests
# ─────────────────────────────────────────────

def test_bookings_drop_pct_normal():
    metrics = {"bookings_this_week": 10, "bookings_last_week": 20}
    assert _bookings_drop_pct(metrics) == pytest.approx(50.0)


def test_bookings_drop_pct_no_last_week():
    metrics = {"bookings_this_week": 10, "bookings_last_week": 0}
    assert _bookings_drop_pct(metrics) == 0.0


def test_bookings_drop_pct_growth():
    # No drop when bookings grew
    metrics = {"bookings_this_week": 25, "bookings_last_week": 20}
    assert _bookings_drop_pct(metrics) == 0.0


def test_peak_hour_lunch():
    assert _is_peak_hour(12, "Monday") is True


def test_peak_hour_dinner():
    assert _is_peak_hour(19, "Tuesday") is True


def test_peak_hour_off():
    assert _is_peak_hour(3, "Monday") is False


def test_peak_hour_weekend():
    assert _is_peak_hour(14, "Saturday") is True


def test_has_active_offer_found():
    offers = [{"title": "Deal", "active": True, "fixed_price": 199}]
    result = _has_active_offer(offers)
    assert result is not None
    assert result["title"] == "Deal"


def test_has_active_offer_none_active():
    offers = [{"title": "Old Deal", "active": False}]
    assert _has_active_offer(offers) is None


# ─────────────────────────────────────────────
# Scoring engine tests
# ─────────────────────────────────────────────

def test_score_no_context():
    store = fresh_store()
    result = score_context("nonexistent-id")
    assert result.action == "no_action"
    assert result.total == 0.0


def test_score_full_dental_context():
    store = fresh_store()
    seed_full_context(store)
    result = score_context("test-001")
    # Should hit: search_spike(4) + bookings_drop(3) + active_offer(2) + peak_hour(2) + price_sensitive(1) = 12
    assert result.total >= 10
    assert result.action in ("launch_offer", "boost_visibility")
    assert "search_spike_gt150" in result.components
    assert "bookings_drop_gt10pct" in result.components


def test_score_only_trigger_no_spike():
    store = fresh_store()
    cid = "test-002"
    store.upsert_context(cid, "merchant", 1, {
        "name": "Generic Merchant",
        "category": "restaurant",
        "city": "Mumbai",
        "metrics": {"bookings_this_week": 20, "bookings_last_week": 18},
        "offers": [],
    })
    store.upsert_context(cid, "trigger", 1, {
        "type": "search_spike",
        "search_count": 80,  # below 150 threshold
        "hour_of_day": 3,
    })
    result = score_context(cid)
    assert "search_spike_gt150" not in result.components


def test_score_competitor_drop():
    store = fresh_store()
    cid = "test-003"
    store.upsert_context(cid, "merchant", 1, {
        "name": "Fit Zone Gym",
        "category": "gym",
        "city": "Delhi",
        "metrics": {"bookings_this_week": 30, "bookings_last_week": 30},
        "offers": [],
    })
    store.upsert_context(cid, "trigger", 1, {
        "type": "competitor_drop",
        "competitor_name": "Iron House Gym",
        "competitor_drop_pct": 20,
    })
    result = score_context(cid)
    assert "competitor_drop" in result.components
    assert result.action == "boost_visibility"


# ─────────────────────────────────────────────
# Versioning tests
# ─────────────────────────────────────────────

def test_version_no_op():
    store = fresh_store()
    r1 = store.upsert_context("v-test", "merchant", 2, {"name": "A"})
    r2 = store.upsert_context("v-test", "merchant", 2, {"name": "A"})
    assert r1 == "inserted"
    assert r2 == "no_op"


def test_version_upgrade():
    store = fresh_store()
    store.upsert_context("v-test2", "merchant", 1, {"name": "Old"})
    r = store.upsert_context("v-test2", "merchant", 2, {"name": "New"})
    assert r == "updated"
    state = store.get_state("v-test2")
    assert state.merchant.data["name"] == "New"


def test_version_stale_ignored():
    store = fresh_store()
    store.upsert_context("v-test3", "merchant", 5, {"name": "Latest"})
    r = store.upsert_context("v-test3", "merchant", 3, {"name": "Old"})
    assert r == "ignored"
    state = store.get_state("v-test3")
    assert state.merchant.data["name"] == "Latest"


# ─────────────────────────────────────────────
# Renderer tests
# ─────────────────────────────────────────────

def test_render_message_dentist():
    merchant = {
        "name": "SmileCare",
        "category": "dentist",
        "city": "Bangalore",
        "locality": "Indiranagar",
        "metrics": {"bookings_this_week": 12, "bookings_last_week": 16, "avg_rating": 4.6},
        "offers": [{"title": "₹299 Checkup", "fixed_price": 299, "active": True}],
    }
    trigger = {"type": "search_spike", "search_count": 190, "search_keyword": "Dental Checkup"}
    customer = {}
    ctx = build_render_context(merchant, trigger, customer)
    msg = render_message("dentist", "launch_offer", 12.0, ctx)
    assert len(msg) <= 220
    assert "190" in msg or "Dental" in msg


def test_render_message_restaurant():
    merchant = {
        "name": "Biryani House",
        "category": "restaurant",
        "city": "Hyderabad",
        "locality": "Banjara Hills",
        "metrics": {"bookings_this_week": 40, "bookings_last_week": 60, "avg_rating": 4.3},
        "offers": [{"title": "Dinner Combo", "fixed_price": 349, "active": True}],
    }
    trigger = {"type": "search_spike", "search_count": 210, "hour_of_day": 20, "day_of_week": "Friday"}
    customer = {}
    ctx = build_render_context(merchant, trigger, customer)
    msg = render_message("restaurant", "launch_offer", 9.0, ctx)
    assert len(msg) <= 220
    assert "210" in msg or "combo" in msg.lower() or "dinner" in msg.lower()


def test_message_hash_stable():
    h1 = message_hash("Hello merchant!")
    h2 = message_hash("Hello merchant!")
    assert h1 == h2


def test_message_hash_different():
    h1 = message_hash("Message A")
    h2 = message_hash("Message B")
    assert h1 != h2
