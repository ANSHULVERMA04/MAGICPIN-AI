"""
Integration tests for all API endpoints.
Run: pytest tests/test_api.py
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage.store import ContextStore

client = TestClient(app)

def setup_function():
    ContextStore._instance = None

def test_healthz():
    r = client.get("/v1/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_metadata():
    r = client.get("/v1/metadata")
    assert r.status_code == 200
    assert "scoring_weights" in r.json()

def test_context_merchant():
    r = client.post("/v1/context", json={
        "context_id": "api-001",
        "scope": "merchant",
        "version": 1,
        "merchant": {
            "name": "SmileCare Dental",
            "category": "dentist",
            "city": "Bangalore",
            "locality": "Indiranagar",
            "metrics": {
                "bookings_this_week": 10,
                "bookings_last_week": 18,
                "avg_rating": 4.6
            },
            "offers": [{"title": "299 Checkup", "fixed_price": 299, "active": True}]
        }
    })
    assert r.status_code == 200
    assert r.json()["result"] == "inserted"

def test_context_idempotent():
    client.post("/v1/context", json={
        "context_id": "api-002", "scope": "merchant", "version": 3,
        "merchant": {"name": "X", "category": "gym", "city": "Delhi"}
    })
    r = client.post("/v1/context", json={
        "context_id": "api-002", "scope": "merchant", "version": 3,
        "merchant": {"name": "X", "category": "gym", "city": "Delhi"}
    })
    assert r.json()["result"] == "no_op"

def test_tick_no_context():
    r = client.post("/v1/tick", json={"context_id": "nonexistent-999"})
    assert r.status_code == 404

def test_full_flow():
    cid = "flow-001"
    client.post("/v1/context", json={
        "context_id": cid, "scope": "merchant", "version": 1,
        "merchant": {
            "name": "Glow Salon", "category": "salon",
            "city": "Mumbai", "locality": "Bandra",
            "metrics": {"bookings_this_week": 8, "bookings_last_week": 15, "avg_rating": 4.4},
            "offers": [{"title": "Weekend Glow", "fixed_price": 499, "active": True}]
        }
    })
    client.post("/v1/context", json={
        "context_id": cid, "scope": "trigger", "version": 1,
        "trigger": {"type": "search_spike", "search_count": 175,
                    "search_keyword": "salon near me", "hour_of_day": 18, "day_of_week": "Saturday"}
    })
    tick = client.post("/v1/tick", json={"context_id": cid})
    assert tick.status_code == 200
    assert tick.json()["score"] > 0

    reply = client.post("/v1/reply", json={"context_id": cid, "dry_run": True})
    assert reply.status_code == 200
    msg = reply.json()["message"]
    assert msg is not None
    assert len(msg) <= 220
