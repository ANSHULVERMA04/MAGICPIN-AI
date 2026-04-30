"""
Magicpin AI Challenge — Merchant Engagement Decision Engine
Entry point: FastAPI application with all registered routes.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.context import router as context_router
from app.routes.tick import router as tick_router
from app.routes.reply import router as reply_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Magicpin Merchant Engagement Engine",
    description="Deterministic AI decision engine for merchant engagement.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/v1")
app.include_router(context_router, prefix="/v1")
app.include_router(tick_router, prefix="/v1")
app.include_router(reply_router, prefix="/v1")


for route in app.routes:
    print(f"Route loaded: {route.path}")

logger.info("Magicpin AI Engine started.")
