"""
Pydantic schemas for all context types.
Covers merchant, trigger, and customer scopes.
"""
from __future__ import annotations
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────
# MERCHANT CONTEXT
# ─────────────────────────────────────────────

class MerchantMetrics(BaseModel):
    bookings_this_week: int = Field(0, ge=0)
    bookings_last_week: int = Field(0, ge=0)
    avg_rating: float = Field(4.0, ge=0.0, le=5.0)
    repeat_customer_pct: float = Field(0.0, ge=0.0, le=100.0)
    monthly_revenue: Optional[float] = None


class MerchantOffer(BaseModel):
    title: str
    discount_pct: Optional[int] = None
    fixed_price: Optional[int] = None  # ₹ price if it's a fixed offer
    valid_until: Optional[str] = None  # ISO date string
    active: bool = True


class MerchantContext(BaseModel):
    name: str
    category: Literal["dentist", "restaurant", "salon", "gym", "pharmacy"]
    city: str
    locality: Optional[str] = None
    metrics: MerchantMetrics = Field(default_factory=MerchantMetrics)
    offers: List[MerchantOffer] = Field(default_factory=list)
    last_message_sent_at: Optional[str] = None  # ISO datetime


# ─────────────────────────────────────────────
# TRIGGER CONTEXT
# ─────────────────────────────────────────────

class TriggerContext(BaseModel):
    type: Literal[
        "search_spike", "weather", "timing", "demand_surge", "competitor_drop"
    ]
    search_count: Optional[int] = None        # for search_spike
    search_keyword: Optional[str] = None      # e.g. "dental checkup"
    weather_condition: Optional[str] = None   # e.g. "rain", "heat"
    hour_of_day: Optional[int] = Field(None, ge=0, le=23)
    day_of_week: Optional[str] = None         # e.g. "Friday"
    demand_multiplier: Optional[float] = None # e.g. 1.4 = 40% surge
    competitor_name: Optional[str] = None
    competitor_drop_pct: Optional[float] = None


# ─────────────────────────────────────────────
# CUSTOMER CONTEXT
# ─────────────────────────────────────────────

class CustomerContext(BaseModel):
    intent: Optional[str] = None          # e.g. "booking", "browsing"
    objection: Optional[str] = None       # e.g. "too expensive", "not sure"
    price_sensitive: bool = False
    responsiveness: Literal["high", "medium", "low"] = "medium"
    past_visits: int = Field(0, ge=0)


# ─────────────────────────────────────────────
# UNIFIED CONTEXT ENVELOPE
# ─────────────────────────────────────────────

class ContextPayload(BaseModel):
    context_id: str = Field(..., min_length=1)
    scope: Literal["merchant", "trigger", "customer"]
    version: int = Field(..., ge=0)
    merchant: Optional[MerchantContext] = None
    trigger: Optional[TriggerContext] = None
    customer: Optional[CustomerContext] = None

    @model_validator(mode="after")
    def validate_scope_data(self) -> "ContextPayload":
        if self.scope == "merchant" and self.merchant is None:
            raise ValueError("scope=merchant requires 'merchant' field")
        if self.scope == "trigger" and self.trigger is None:
            raise ValueError("scope=trigger requires 'trigger' field")
        if self.scope == "customer" and self.customer is None:
            raise ValueError("scope=customer requires 'customer' field")
        return self


# ─────────────────────────────────────────────
# TICK / REPLY REQUESTS
# ─────────────────────────────────────────────

class TickRequest(BaseModel):
    context_id: str = Field(..., min_length=1)


class ReplyRequest(BaseModel):
    context_id: str = Field(..., min_length=1)
    dry_run: bool = False  # if True, does not persist cooldown
