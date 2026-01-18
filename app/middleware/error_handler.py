"""
Global error handling middleware.
Provides consistent error responses across the application.
"""
import traceback
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorResponse:
    """
    Standardized error response format.

    All error responses follow this structure for consistency.
    """

    @staticmethod
    def create(
        success: bool,
        message: str,
        error_code: str | None = None,
        details: Dict[str, Any] | None = None,
        stack: str | None = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response dictionary.

        Args:
            success: Always False for errors
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            stack: Stack trace (only in development)

        Returns:
            Error response dictionary
        """
        response: Dict[str, Any] = {
            "success": success,
            "message": message
        }

        if error_code:
            response["error_code"] = error_code

        if details:
            response["details"] = details

        if stack and settings.is_development:
            response["stack"] = stack

        return response


async def app_exception_handler(
    request: Request,
    exc: AppException
) -> JSONResponse:
    """
    Handle custom application exceptions.

    Logs the error and returns a structured response.
    """
    logger.warning(
        "Application exception",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        path=str(request.url.path),
        method=request.method,
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.create(
            success=False,
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Transforms validation errors into a user-friendly format.
    """
    errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.info(
        "Validation error",
        path=str(request.url.path),
        method=request.method,
        errors=errors
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create(
            success=False,
            message="Validation error",
            error_code="ValidationError",
            details={"errors": errors}
        )
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle standard HTTP exceptions.

    Transforms Starlette HTTP exceptions into our format.
    """
    logger.info(
        "HTTP exception",
        path=str(request.url.path),
        method=request.method,
        status_code=exc.status_code,
        detail=str(exc.detail)
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.create(
            success=False,
            message=str(exc.detail),
            error_code=f"HTTP{exc.status_code}"
        )
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unhandled exceptions.

    Catches all other exceptions and returns a generic error.
    Stack trace is only included in development mode.
    """
    stack_trace = traceback.format_exc()

    logger.error(
        "Unhandled exception",
        path=str(request.url.path),
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        traceback=stack_trace
    )

    # In production, hide internal error details
    if settings.is_production:
        message = "Internal server error"
        stack = None
    else:
        message = str(exc)
        stack = stack_trace

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.create(
            success=False,
            message=message,
            error_code="InternalServerError",
            stack=stack
        )
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
