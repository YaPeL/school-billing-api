from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.domain.errors import ConflictError, DomainError, NotFoundError


async def not_found_error_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message()},
    )


async def conflict_error_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message()},
    )


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, cast(Any, not_found_error_handler))
    app.add_exception_handler(ConflictError, cast(Any, conflict_error_handler))
    app.add_exception_handler(DomainError, cast(Any, domain_error_handler))
