"""
Deterministic message templates, keyed by (category, action).
Templates use named string format keys that are resolved at render time.
Gold standard: specific numbers, offers, city facts, one CTA.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Template format keys available to all templates:
#   {search_count}      int — searches detected
#   {search_keyword}    str — e.g. "Dental Checkup"
#   {merchant_name}     str
#   {city}              str
#   {locality}          str  (falls back to city)
#   {drop_pct}          str  e.g. "18%"
#   {offer_title}       str
#   {offer_price}       str  e.g. "₹299"
#   {offer_discount}    str  e.g. "30%"
#   {rating}            str  e.g. "4.6"
#   {this_week}         int
#   {last_week}         int
#   {hour}              int
#   {day}               str  e.g. "Friday"
#   {competitor}        str
# ─────────────────────────────────────────────────────────────────────────────

# Structure: {(category, action): [list of template strings]}
# Multiple templates allow deterministic selection by score tier.

TEMPLATES: Dict[Tuple[str, str], List[str]] = {

    # ─── DENTIST ─────────────────────────────────────────────────────────

    ("dentist", "launch_offer"): [
        "{search_count} people nearby searched '{search_keyword}' today. "
        "Your bookings are down {drop_pct} this week. "
        "Launch ₹{offer_price} checkup offer now?",

        "{search_count} dental searches near {locality} today — "
        "bookings down {drop_pct} vs last week. "
        "Activate your checkup offer to convert them?",

        "High demand for dental care near {locality} ({search_count} searches). "
        "Launch a ₹{offer_price} family checkup offer before your competitors do?",
    ],
    ("dentist", "boost_visibility"): [
        "{search_count} people searched for dental clinics near {locality} today. "
        "Your '{offer_title}' is live — boost now to reach them first?",

        "Dental search spike near {city}: {search_count} searches. "
        "Your {rating}⭐ rating is a trust signal — boost visibility now?",
    ],
    ("dentist", "reply_to_query"): [
        "A patient may be waiting. Reply to pending queries in the next 10 min "
        "to lock in a booking — {this_week} booked this week so far.",

        "Peak consultation hour in {city}. Fast replies = more bookings. "
        "Respond now to stay ahead of nearby clinics?",
    ],
    ("dentist", "collect_review"): [
        "Your {rating}⭐ rating drives trust. Send a quick post-visit review "
        "request to your last 5 patients. One extra ⭐ = 12% more bookings.",
    ],

    # ─── RESTAURANT ──────────────────────────────────────────────────────

    ("restaurant", "launch_offer"): [
        "{search_count} people near {locality} are searching for dinner now. "
        "Bookings are down {drop_pct}. Launch a ₹{offer_price} combo deal tonight?",

        "Dinner rush is on — {search_count} searches near {city} in the last hour. "
        "Your bookings are {drop_pct} below last week. Run a combo offer to fill tables?",

        "{search_count} hungry customers searched near {locality} today. "
        "Drop a ₹{offer_price} weekend special to turn searches into orders?",
    ],
    ("restaurant", "boost_visibility"): [
        "It's {day} evening — {search_count} searches near {locality}. "
        "Your '{offer_title}' is live. Boost now to appear #1 when cravings hit?",

        "High dinner demand near {city} ({search_count} searches). "
        "Boost visibility for 2 hours to capture the rush?",
    ],
    ("restaurant", "reply_to_query"): [
        "Someone's asking about your menu right now. "
        "Quick reply = confirmed order. {this_week} orders placed this week — keep it going?",
    ],
    ("restaurant", "collect_review"): [
        "Post-meal reviews drive repeat orders. "
        "Ask your last 10 customers for a review — {rating}⭐ can go higher!",
    ],

    # ─── SALON ───────────────────────────────────────────────────────────

    ("salon", "launch_offer"): [
        "{search_count} people near {locality} searched for salon services today. "
        "Bookings down {drop_pct}. Launch a ₹{offer_price} weekend style offer now?",

        "Pre-weekend demand is up — {search_count} searches near {city}. "
        "Drop a {offer_discount}% off offer to fill your {day} slots?",

        "{search_count} style-seekers near {locality} today. "
        "Your bookings slipped {drop_pct} this week — a fresh offer can turn that around?",
    ],
    ("salon", "boost_visibility"): [
        "Weekend bookings start now. {search_count} searches near {locality}. "
        "Boost your '{offer_title}' to appear first before slots fill up?",
    ],
    ("salon", "reply_to_query"): [
        "A customer is browsing your services. "
        "Reply now to lock in their slot — {this_week} bookings this week already.",
    ],
    ("salon", "collect_review"): [
        "Happy clients are your best ads. "
        "Send a review reminder to your last 5 visitors — your {rating}⭐ can climb higher.",
    ],

    # ─── GYM ─────────────────────────────────────────────────────────────

    ("gym", "launch_offer"): [
        "{search_count} people near {locality} searched for gyms today. "
        "Memberships down {drop_pct}. Launch a ₹{offer_price} 7-day trial now?",

        "New Year, new goals — {search_count} gym searches near {city} today. "
        "Offer a free trial week to convert interest into members?",

        "{search_count} fitness searches near {locality}. "
        "Bookings down {drop_pct} — a ₹{offer_price} trial offer could turn this around fast.",
    ],
    ("gym", "boost_visibility"): [
        "{search_count} fitness searches near {city} today. "
        "Boost '{offer_title}' visibility now to catch the motivation wave?",

        "Peak fitness motivation hour. {search_count} searches near {locality}. "
        "Boost now to be the first gym they see?",
    ],
    ("gym", "reply_to_query"): [
        "Someone's asking about your trial offer. "
        "Reply in 5 min = 3x conversion. You've had {this_week} sign-ups this week — add one more?",
    ],
    ("gym", "collect_review"): [
        "Member reviews drive new sign-ups more than ads. "
        "Ask your regulars for a quick review — your {rating}⭐ rating is a strong start.",
    ],

    # ─── PHARMACY ────────────────────────────────────────────────────────

    ("pharmacy", "launch_offer"): [
        "{search_count} people near {locality} searched for medicines today. "
        "Sales down {drop_pct}. Activate your ₹{offer_price} essentials bundle offer?",

        "High demand near {city} — {search_count} pharmacy searches today. "
        "Run a quick essentials offer to drive walk-ins this evening?",

        "{search_count} health-related searches near {locality} today. "
        "Sales slipped {drop_pct} — drop a {offer_discount}% off essentials offer now?",
    ],
    ("pharmacy", "boost_visibility"): [
        "Evening medication rush near {locality} — {search_count} searches. "
        "Boost '{offer_title}' to be the closest, most visible pharmacy?",
    ],
    ("pharmacy", "reply_to_query"): [
        "A customer is asking about availability. "
        "Quick reply = guaranteed visit. You had {this_week} walk-ins this week.",
    ],
    ("pharmacy", "collect_review"): [
        "Trust is everything in pharmacy. "
        "Ask your last 10 customers for a review — {rating}⭐ builds confidence fast.",
    ],
}


_FALLBACK: Dict[str, str] = {
    "launch_offer":    "{search_count} potential customers near {locality} today. "
                       "Bookings are down {drop_pct}. Activate an offer to convert them?",
    "boost_visibility": "{search_count} searches near {locality}. "
                        "Boost visibility now to capture demand?",
    "reply_to_query":  "A customer is waiting. Reply now to convert interest into a booking.",
    "collect_review":  "Ask your recent customers for a review. "
                       "Social proof drives more bookings.",
    "no_action":       "All signals normal. No action needed right now.",
}


def get_template(category: str, action: str, score: float) -> str:
    """
    Returns the best template for (category, action).
    Uses score tier to pick among variants (highest score → most urgent variant).
    """
    variants = TEMPLATES.get((category, action))
    if not variants:
        return _FALLBACK.get(action, "Check your dashboard for new opportunities.")

    
    if score >= 8:
        idx = min(2, len(variants) - 1)
    elif score >= 5:
        idx = min(1, len(variants) - 1)
    else:
        idx = 0

    return variants[idx]
