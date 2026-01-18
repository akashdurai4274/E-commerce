"""
Request/Response logging middleware.
Logs all incoming requests and outgoing responses with timing.
"""
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Logs request details on entry and response details with timing on exit.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Skip logging for health check endpoints
        if request.url.path in ["/health", "/api/health", "/favicon.ico"]:
            return await call_next(request)

        # Record start time
        start_time = time.perf_counter()

        # Get request details
        request_id = request.headers.get("X-Request-ID", "-")
        client_ip = request.client.host if request.client else "unknown"

        # Log incoming request
        logger.info(
            "Request started",
            method=request.method,
            path=str(request.url.path),
            query=str(request.url.query) if request.url.query else None,
            client_ip=client_ip,
            request_id=request_id,
            user_agent=request.headers.get("user-agent", "-")[:100]
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = (time.perf_counter() - start_time) * 1000  # ms

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(process_time, 2),
            request_id=request_id
        )

        # Add timing header to response
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response
