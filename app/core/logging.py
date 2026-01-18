"""
Structured logging configuration using structlog.
Provides JSON and text formatters for different environments.
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure application logging with structlog.

    Sets up JSON logging for production and readable text for development.
    """
    # Shared processors for both handlers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        # JSON format for production
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        # Human-readable format for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LoggerAdapter:
    """
    Logger adapter that adds context to all log messages.

    Useful for adding request-specific context like user_id, request_id.
    """

    def __init__(self, logger: structlog.BoundLogger, extra: dict[str, Any]):
        self._logger = logger
        self._extra = extra

    def _log(self, method: str, msg: str, **kwargs: Any) -> None:
        """Internal method to add extra context to logs."""
        kwargs.update(self._extra)
        getattr(self._logger, method)(msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("debug", msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("error", msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception with stack trace."""
        self._log("exception", msg, **kwargs)

    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """Create new adapter with additional context."""
        extra = {**self._extra, **kwargs}
        return LoggerAdapter(self._logger, extra)


def create_logger_with_context(name: str, **context: Any) -> LoggerAdapter:
    """
    Create a logger with pre-bound context.

    Args:
        name: Logger name
        **context: Key-value pairs to include in all log messages

    Returns:
        LoggerAdapter with bound context
    """
    base_logger = get_logger(name)
    return LoggerAdapter(base_logger, context)
