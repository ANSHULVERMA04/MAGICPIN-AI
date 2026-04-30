# Magicpin AI — Merchant Engagement Decision Engine

A deterministic AI decision engine that scores merchant contexts, selects the best action, and generates highly specific merchant-facing messages.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /v1/healthz | Health check |
| GET | /v1/metadata | Engine metadata & scoring weights |
| POST | /v1/context | Ingest merchant/trigger/customer context |
| POST | /v1/tick | Run scoring engine, select action |
| POST | /v1/reply | Generate merchant-facing message |

## Scoring Weights

| Signal | Points |
|--------|--------|
| Search spike > 150 | +4 |
| Bookings drop > 10% | +3 |
| Active offer exists | +2 |
| Peak hour | +2 |
| Demand surge ≥ 1.2x | up to +3 |
| Competitor drop ≥ 15% | +2 |
| Price-sensitive customer | +1 |
| Repeat message penalty | -5 |

## Supported Categories

`dentist` · `restaurant` · `salon` · `gym` · `pharmacy`

## Run Tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t magicpin-engine .
docker run -p 8000:8000 magicpin-engine
```

## Railway Deployment

1. Push to GitHub
2. Connect repo to Railway
3. Railway auto-detects Dockerfile
4. Set `PORT=8000` env var
5. Deploy — done

## Sample Curl Requests

```bash
bash curl_examples.sh
```

## Architecture

```
app/
├── main.py              # FastAPI app
├── routes/
│   ├── health.py        # GET /healthz, /metadata
│   ├── context.py       # POST /context
│   ├── tick.py          # POST /tick
│   └── reply.py         # POST /reply
├── schemas/
│   └── context_schema.py  # Pydantic models
├── engine/
│   ├── scorer.py        # Deterministic scoring
│   ├── templates.py     # Category-aware templates
│   └── renderer.py      # Message rendering
├── storage/
│   └── store.py         # In-memory versioned store
└── utils/
    └── time_utils.py
tests/
├── test_engine.py       # Unit tests
└── test_api.py          # Integration tests
```

## Message Gold Standard

> 190 people nearby searched 'Dental Checkup' today. Your bookings are down 40% this week. Launch ₹299 checkup offer now?

- Specific numbers ✓
- Category-aware copy ✓
- One clear CTA ✓
- Under 220 chars ✓
