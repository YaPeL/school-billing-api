import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.core.logging import configure_logging
from app.core.observability import request_logging_middleware
from app.core.settings import settings

configure_logging()

app = FastAPI(title="Mattilda Backend")

app.middleware("http")(request_logging_middleware)

app.include_router(health_router, tags=["health"])
app.include_router(metrics_router, tags=["metrics"])

log = logging.getLogger("app")

if settings.jwt_secret == "change_me":
    log.warning("JWT_SECRET is set to 'change_me' (demo default). Do not use in production.")
