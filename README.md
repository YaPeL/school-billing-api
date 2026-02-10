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

## Auth (demo JWT)
- Login:
  - `curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"change_me"}'`
- Use token for write endpoints:
  - `curl -X POST http://localhost:8000/schools -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"name":"Springfield Elementary"}'`
- Read endpoints remain public (`GET` schools/students/invoices/payments, statements, health, metrics).

## Notes
- Observability: structured logs + /health + /metrics
- Payments are first-class (partial payments supported)
