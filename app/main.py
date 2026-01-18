"""
FastAPI Application Entry Point.

This is the main entry point for the SkyCart FastAPI backend.
It configures the application with all middleware, routes, and dependencies.

Architecture Notes:
- Uses Clean/Hexagonal Architecture
- Dependency injection via FastAPI's Depends
- Async MongoDB with Motor
- Centralized error handling
- Structured logging with correlation IDs
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.dependencies import init_database, close_database
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.correlation_id import CorrelationIdMiddleware

# Import API routers
from app.api.v1 import api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database, configure logging
    - Shutdown: Close database connections

    This is the modern FastAPI way to handle startup/shutdown
    instead of deprecated @app.on_event decorators.
    """
    # Startup
    logger.info(
        "Starting SkyCart API",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG
    )

    # Configure logging based on environment
    setup_logging()

    # Initialize database connection and create indexes
    await init_database()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down SkyCart API")
    await close_database()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    Application factory function.

    Creates and configures the FastAPI application instance.
    Using a factory pattern allows for:
    - Easy testing with different configurations
    - Clean separation of concerns
    - Reusable application creation logic
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-grade e-commerce API built with FastAPI",
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware (order matters - last added is first executed)
    # So: CorrelationId -> Logging -> (request handling) -> Logging -> CorrelationId
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # Register exception handlers
    register_exception_handlers(app)

    # Mount static files for uploads
    # app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # Include API routers
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.

        Used by load balancers and monitoring systems.
        Returns basic application status.
        """
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/api/docs" if settings.DEBUG else "Disabled in production"
        }

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
