"""Health and metadata endpoints."""
import logging
from fastapi import APIRouter
from app.storage.store import ContextStore

router = APIRouter(tags=["System"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthz():
    store = ContextStore.get_instance()
    return {
        "status": "ok",
        "context_count": store.count(),
    }


@router.get("/metadata")
def metadata():
    return {
        "engine": "Magicpin Merchant Engagement Engine",
        "version": "1.0.0",
        "supported_categories": [
            "dentist", "restaurant", "salon", "gym", "pharmacy"
        ],
        "supported_triggers": [
            "search_spike", "weather", "timing", "demand_surge", "competitor_drop"
        ],
        "scoring_weights": {
            "search_spike_gt150": 4,
            "bookings_drop_gt10pct": 3,
            "active_offer": 2,
            "peak_hour": 2,
            "repeat_message_penalty": -5,
            "customer_price_sensitive": 1,
        },
        "endpoints": [
            "GET  /v1/healthz",
            "GET  /v1/metadata",
            "POST /v1/context",
            "POST /v1/tick",
            "POST /v1/reply",
        ],
    }
