# Mattilda Backend Challenge

## Requirements
- Python 3.12
- Poetry
- Docker + Docker Compose

## Setup
- poetry install
- pre-commit install

## Run (local)
- docker compose up -d db
- poetry run uvicorn app.main:app --reload

Open:
- http://localhost:8000/docs
- http://localhost:8000/health
- http://localhost:8000/health/db
- http://localhost:8000/metrics

## Run (docker)
- docker compose up --build

## Tests
- Fast tests (no DB):
  - poetry run pytest -m smoke

## Notes
- Observability: structured logs + /health + /metrics
- Payments are first-class (partial payments supported)
