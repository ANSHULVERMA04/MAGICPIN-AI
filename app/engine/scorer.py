"""
Deterministic scoring engine.
Evaluates all available signals and returns a ranked action + score breakdown.
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.storage.store import ContextStore, MerchantState, COOLDOWN_SECONDS

logger = logging.getLogger(__name__)


ACTIONS = [
    "launch_offer",        
    "boost_visibility",    
    "reply_to_query",      
    "update_menu_photos", 
    "collect_review",      
    "no_action",           
]


@dataclass
class ScoreBreakdown:
    action: str
    total: float
    components: Dict[str, float] = field(default_factory=dict)
    rationale: List[str] = field(default_factory=list)


def _bookings_drop_pct(metrics: Dict[str, Any]) -> float:
    """Returns percentage drop in bookings week-over-week (positive = drop)."""
    this_week = metrics.get("bookings_this_week", 0) or 0
    last_week = metrics.get("bookings_last_week", 0) or 0
    if last_week <= 0:
        return 0.0
    return max(0.0, (last_week - this_week) / last_week * 100)


def _is_peak_hour(hour: Optional[int], day: Optional[str]) -> bool:
    if hour is None:
        return False
   
    if 11 <= hour <= 14:
        return True
    if 18 <= hour <= 21:
        return True
    if day in ("Saturday", "Sunday") and 10 <= hour <= 22:
        return True
    return False


def _has_active_offer(offers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for offer in offers:
        if offer.get("active", False):
            return offer
    return None


def _cooldown_active(state: MerchantState) -> bool:
    if state.last_message_at is None:
        return False
    return (time.time() - state.last_message_at) < COOLDOWN_SECONDS


def score_context(context_id: str) -> ScoreBreakdown:
    """
    Run the full scoring pipeline for a context_id.
    Returns the best ScoreBreakdown.
    """
    store = ContextStore.get_instance()
    state = store.get_state(context_id)

    if state is None:
        return ScoreBreakdown(action="no_action", total=0.0, rationale=["No context found"])

    # Pull raw dicts from stored records
    merchant_data: Dict[str, Any] = state.merchant.data if state.merchant else {}
    trigger_data: Dict[str, Any] = state.trigger.data if state.trigger else {}
    customer_data: Dict[str, Any] = state.customer.data if state.customer else {}

    metrics = merchant_data.get("metrics", {}) or {}
    offers = merchant_data.get("offers", []) or []
    trigger_type = trigger_data.get("type", "")
    search_count = trigger_data.get("search_count") or 0
    hour = trigger_data.get("hour_of_day")
    day = trigger_data.get("day_of_week")

    components: Dict[str, float] = {}
    rationale: List[str] = []

  
    if trigger_type == "search_spike" and search_count > 150:
        components["search_spike_gt150"] = 4.0
        keyword = trigger_data.get("search_keyword", "your category")
        rationale.append(f"{search_count} searches for '{keyword}' detected nearby")

    
    drop_pct = _bookings_drop_pct(metrics)
    if drop_pct > 10:
        components["bookings_drop_gt10pct"] = 3.0
        rationale.append(f"Bookings dropped {drop_pct:.0f}% vs last week")

   
    active_offer = _has_active_offer(offers)
    if active_offer:
        components["active_offer"] = 2.0
        rationale.append(f"Active offer available: '{active_offer.get('title', 'Offer')}'")

   
    if _is_peak_hour(hour, day):
        components["peak_hour"] = 2.0
        rationale.append(f"Peak hour detected (hour={hour}, day={day})")

    
    if trigger_type == "demand_surge":
        multiplier = trigger_data.get("demand_multiplier", 1.0) or 1.0
        if multiplier >= 1.2:
            bonus = round(min((multiplier - 1.0) * 10, 3.0), 1)
            components["demand_surge"] = bonus
            rationale.append(f"Demand surge x{multiplier:.1f} detected")

    
    if trigger_type == "competitor_drop":
        drop = trigger_data.get("competitor_drop_pct", 0) or 0
        if drop >= 15:
            components["competitor_drop"] = 2.0
            comp = trigger_data.get("competitor_name", "a nearby competitor")
            rationale.append(f"{comp} dropped ratings by {drop:.0f}% — opportunity window")

  
    if customer_data.get("price_sensitive"):
        components["price_sensitive_customer"] = 1.0
        rationale.append("Customer is price-sensitive — discount offer is compelling")
        
        

   
    if _cooldown_active(state):
        components["repeat_message_penalty"] = -5.0
        rationale.append("Merchant messaged recently — cooldown penalty applied")

    total = sum(components.values())

  
    action = _select_action(total, trigger_type, active_offer, drop_pct, components)

    logger.info(
        "context_id=%s action=%s score=%.1f components=%s",
        context_id, action, total, components,
    )
    return ScoreBreakdown(action=action, total=total, components=components, rationale=rationale)


def _select_action(
    total: float,
    trigger_type: str,
    active_offer: Optional[Dict],
    drop_pct: float,
    components: Dict[str, float],
) -> str:
    """
    Deterministic action selector — highest-signal action wins.
    No randomness.
    """
    if total < 1.0:
        return "no_action"

    
    if components.get("search_spike_gt150", 0) >= 4 and drop_pct > 5:
        return "launch_offer"

    
    if active_offer and total >= 4:
        return "boost_visibility"

   
    if components.get("bookings_drop_gt10pct", 0) >= 3:
        return "launch_offer"

   
    if trigger_type in ("competitor_drop", "demand_surge"):
        return "boost_visibility"

   
    if components.get("peak_hour", 0) >= 2:
        return "reply_to_query"


    if total >= 1:
        return "collect_review"

    return "no_action"
