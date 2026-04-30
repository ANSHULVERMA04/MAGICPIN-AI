"""
Template renderer.
Resolves all {key} placeholders from the merged context.
Deterministic — same context always produces the same message.
"""
from __future__ import annotations
import hashlib
import logging
from typing import Any, Dict, Optional

from app.engine.templates import get_template
from app.engine.scorer import ScoreBreakdown, _has_active_offer, _bookings_drop_pct

logger = logging.getLogger(__name__)


def _safe_fmt(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    return str(value)


def build_render_context(
    merchant_data: Dict[str, Any],
    trigger_data: Dict[str, Any],
    customer_data: Dict[str, Any],
) -> Dict[str, str]:
    """
    Builds the flat dict of all substitution keys from structured context dicts.
    Every value is a safe string — KeyError on format is impossible.
    """
    metrics = merchant_data.get("metrics", {}) or {}
    offers = merchant_data.get("offers", []) or []
    active_offer = _has_active_offer(offers) or {}
    drop_pct = _bookings_drop_pct(metrics)

    # Offer price resolution: fixed_price takes precedence over discount
    offer_price = (
        active_offer.get("fixed_price")
        or active_offer.get("discount_pct")
        or "—"
    )
    offer_discount = active_offer.get("discount_pct") or "—"

    locality = merchant_data.get("locality") or merchant_data.get("city", "your area")

    ctx: Dict[str, str] = {
        # Merchant
        "merchant_name": _safe_fmt(merchant_data.get("name"), "Your Business"),
        "city":          _safe_fmt(merchant_data.get("city"), "your city"),
        "locality":      _safe_fmt(locality),
        "rating":        _safe_fmt(metrics.get("avg_rating"), "4.5"),
        "this_week":     _safe_fmt(metrics.get("bookings_this_week"), "0"),
        "last_week":     _safe_fmt(metrics.get("bookings_last_week"), "0"),
        "drop_pct":      f"{drop_pct:.0f}%",

        # Offer
        "offer_title":    _safe_fmt(active_offer.get("title"), "Special Offer"),
        "offer_price":    _safe_fmt(offer_price),
        "offer_discount": _safe_fmt(offer_discount),

        # Trigger
        "search_count":    _safe_fmt(trigger_data.get("search_count"), "100+"),
        "search_keyword":  _safe_fmt(
            trigger_data.get("search_keyword"),
            merchant_data.get("category", "your service"),
        ),
        "hour":         _safe_fmt(trigger_data.get("hour_of_day")),
        "day":          _safe_fmt(trigger_data.get("day_of_week"), "today"),
        "competitor":   _safe_fmt(trigger_data.get("competitor_name"), "a nearby competitor"),
    }
    return ctx


def render_message(
    category: str,
    action: str,
    score: float,
    render_ctx: Dict[str, str],
) -> str:
    """
    Renders the message template for (category, action) using render_ctx.
    Truncates to 220 chars if needed, preserving sentence integrity.
    """
    template = get_template(category, action, score)
    try:
        message = template.format_map(render_ctx)
    except KeyError as exc:
        logger.warning("Template key missing: %s — using safe fallback", exc)
        # Build a safe default using only guaranteed keys
        message = (
            f"{render_ctx.get('search_count', '?')} searches near "
            f"{render_ctx.get('locality', 'your area')} today. "
            f"Bookings down {render_ctx.get('drop_pct', '?')}. "
            f"Take action now to stay ahead?"
        )

    # Soft truncation at 220 chars — cut at last sentence boundary if possible
    if len(message) > 220:
        truncated = message[:217]
        last_dot = truncated.rfind(".")
        if last_dot > 150:
            message = truncated[:last_dot + 1]
        else:
            message = truncated + "…"

    return message


def message_hash(message: str) -> str:
    """Stable hash for anti-repeat deduplication."""
    return hashlib.sha256(message.encode()).hexdigest()[:16]
