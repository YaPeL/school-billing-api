# STATUS

## Running
- Install:
  - poetry install
  - pre-commit install
- Run (local):
  - docker compose up -d db
  - poetry run uvicorn app.main:app --reload
- Run (docker):
  - docker compose up --build
- Tests:
  - poetry run pytest -m smoke
  - poetry run pytest -m "smoke or integration" (optional)

## Implemented
- Bootstrap project structure
- Settings + logging middleware
- /health, /health/db, /metrics

## Pending
- See PLAN.md
