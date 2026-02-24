Implement demo JWT auth (admin role) and protect non-read endpoints.

Scope:
- Add auth module:
  - app/core/security.py (JWT encode/decode, password hashing optional)
  - app/api/deps.py (get_current_user dependency)
  - app/schemas/auth.py (Token, LoginRequest, UserClaims)
- Env/settings:
  - Use settings.jwt_secret (already exists). Add settings.jwt_algorithm default "HS256".
  - Optional: settings.admin_token_ttl_minutes default 60.
- Add endpoint:
  - POST /auth/login -> returns access token
    - Accepts JSON { "username": "admin", "password": "<ADMIN_PASSWORD>" }
    - ADMIN_PASSWORD comes from env/settings (default "change_me" but warn in logs).
    - Token includes "sub" (username) and "role" ("admin") and exp.
- Authorization rules:
  - Read-only endpoints remain public:
    - GET /health, GET /health/db, GET /metrics
    - GET list/detail for schools/students/invoices/payments
    - GET statements endpoints
  - Write endpoints require admin JWT:
    - POST/PATCH/DELETE for schools/students/invoices/payments
- Implementation details:
  - Add dependency `require_admin` (Depends(get_current_user) + role check).
  - If missing/invalid token -> 401 with standard detail.
  - If token valid but role != admin -> 403.
  - Use FastAPI OAuth2PasswordBearer or HTTPBearer; prefer HTTPBearer for JSON login simplicity.
  - Keep it simple: no DB user table.
- Tests:
  - Add smoke tests (httpx ASGI) for:
    - POST /schools returns 401 without token
    - POST /auth/login returns token with correct creds
    - POST /schools returns 200 with Bearer token (DAL mocked like existing tests)
  - No real DB.
- Docs:
  - Update README with auth usage example (login + Authorization header).
  - Update DECISIONS.md if needed.

Constraints:
- ruff + mypy + pytest -m smoke must pass.
- Do not introduce paid services.
