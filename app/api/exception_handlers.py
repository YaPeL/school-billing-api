from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

from app.api.exceptions import NotFoundError


async def not_found_error_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message()},
    )
