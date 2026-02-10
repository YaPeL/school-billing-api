import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram

logger = logging.getLogger("app.request")

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.perf_counter()

    try:
        response = await call_next(request)
    finally:
        elapsed = time.perf_counter() - start
        path = request.url.path
        method = request.method

        status = getattr(locals().get("response", None), "status_code", 500)
        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=str(status)).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(elapsed)

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status": status,
                "latency_ms": round(elapsed * 1000, 2),
            },
        )

    response.headers["x-request-id"] = request_id
    return response
