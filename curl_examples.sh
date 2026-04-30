#!/bin/bash
# Sample curl requests for all endpoints
BASE="http://localhost:8000"

echo "=== Health Check ==="
curl -s "$BASE/v1/healthz" | python3 -m json.tool

echo -e "\n=== Metadata ==="
curl -s "$BASE/v1/metadata" | python3 -m json.tool

echo -e "\n=== POST Merchant Context ==="
curl -s -X POST "$BASE/v1/context" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "merchant-bangalore-001",
    "scope": "merchant",
    "version": 1,
    "merchant": {
      "name": "SmileCare Dental",
      "category": "dentist",
      "city": "Bangalore",
      "locality": "Indiranagar",
      "metrics": {
        "bookings_this_week": 12,
        "bookings_last_week": 20,
        "avg_rating": 4.6,
        "repeat_customer_pct": 55
      },
      "offers": [
        {"title": "Family Checkup", "fixed_price": 299, "active": true}
      ]
    }
  }' | python3 -m json.tool

echo -e "\n=== POST Trigger Context ==="
curl -s -X POST "$BASE/v1/context" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "merchant-bangalore-001",
    "scope": "trigger",
    "version": 1,
    "trigger": {
      "type": "search_spike",
      "search_count": 190,
      "search_keyword": "Dental Checkup",
      "hour_of_day": 19,
      "day_of_week": "Friday"
    }
  }' | python3 -m json.tool

echo -e "\n=== POST Customer Context ==="
curl -s -X POST "$BASE/v1/context" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "merchant-bangalore-001",
    "scope": "customer",
    "version": 1,
    "customer": {
      "intent": "booking",
      "price_sensitive": true,
      "responsiveness": "high",
      "past_visits": 0
    }
  }' | python3 -m json.tool

echo -e "\n=== POST Tick ==="
curl -s -X POST "$BASE/v1/tick" \
  -H "Content-Type: application/json" \
  -d '{"context_id": "merchant-bangalore-001"}' | python3 -m json.tool

echo -e "\n=== POST Reply ==="
curl -s -X POST "$BASE/v1/reply" \
  -H "Content-Type: application/json" \
  -d '{"context_id": "merchant-bangalore-001", "dry_run": false}' | python3 -m json.tool
