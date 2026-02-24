Add CI + badges + README polish to finalize the backend repo for submission.

Goals:
- GitHub Actions CI:
  - Run on push + PR to main
  - Use Python 3.12 (only)
  - Install deps with Poetry
  - Run:
    - poetry run ruff check .
    - poetry run mypy .
    - poetry run pytest -m smoke
- Badges (README):
  - Add CI status badge (GitHub Actions workflow)
  - Add a mypy/type-check badge (static shields badge is OK)
  - Add a tests badge (static shields badge is OK, CI is the source of truth)
  - Add a TODO note for coverage badge (future)
- Docs:
  - README: tighten quickstart and include:
    - docker compose up -d db
    - poetry run db-upgrade
    - poetry run db-seed
    - run API
    - auth/login example + calling protected endpoints with Bearer token
  - Update STATUS.md/PLAN.md if needed to reflect CI is in place.
- TODOs / Pending:
  - Add explicit TODOs for:
    - integration tests (real DB) marked `integration`
    - caching approach for statements (what we'd cache, invalidation strategy)

Constraints:
- Do not change API contracts.
- Keep local dev fast.
- pre-commit must still pass.
