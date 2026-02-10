from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.exception_handlers import not_found_error_handler
from app.api.exceptions import NotFoundError
from app.api.health import router as health_router
from app.api.invoices import router as invoices_router
from app.api.metrics import router as metrics_router
from app.api.payments import router as payments_router
from app.api.schools import router as schools_router
from app.api.students import router as students_router
from app.core.logging import configure_logging
from app.core.observability import request_logging_middleware
from app.core.settings import settings

configure_logging()
log = logging.getLogger("app")

app = FastAPI(title="Mattilda Backend")

app.middleware("http")(request_logging_middleware)

app.include_router(health_router, tags=["health"])
app.include_router(metrics_router, tags=["metrics"])
app.include_router(schools_router)
app.include_router(students_router)
app.include_router(invoices_router)
app.include_router(payments_router)

app.add_exception_handler(NotFoundError, not_found_error_handler)

if settings.jwt_secret == "change_me":
    log.warning("JWT_SECRET is set to 'change_me' (demo default). Do not use in production.")
