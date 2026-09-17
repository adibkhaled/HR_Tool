import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.app.core.correlation import reset_correlation_id, set_correlation_id
from backend.app.core.metrics import metrics_registry

logger = logging.getLogger("hr_tool.request")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        request.state.correlation_id = correlation_id
        token = set_correlation_id(correlation_id)
        started = perf_counter()
        try:
            response = await call_next(request)
            metrics_registry.increment("hr_tool_requests_total")
            metrics_registry.increment(f"hr_tool_requests_{response.status_code}_total")
            return response
        finally:
            elapsed = perf_counter() - started
            metrics_registry.observe("hr_tool_request_duration_seconds", elapsed)
            if "response" in locals():
                response.headers["X-Correlation-ID"] = correlation_id
                logger.info(
                    "%s %s %s",
                    request.method,
                    request.url.path,
                    response.status_code,
                    extra={"correlation_id": correlation_id},
                )
            reset_correlation_id(token)
