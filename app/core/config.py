"""
Application configuration using Pydantic Settings.
Environment-based configuration with validation.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings using Pydantic v2 BaseSettings.

    All settings can be overridden via environment variables.
    Supports .env files for local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ===================
    # Application Settings
    # ===================
    APP_NAME: str = "SkyCart API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Enterprise E-Commerce Backend API"
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|staging|production)$"
    )
    DEBUG: bool = True

    # ===================
    # Server Settings
    # ===================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # ===================
    # URL Settings
    # ===================
    BACKEND_URL: str = "http://127.0.0.1:8000"
    FRONTEND_URL: str = "http://127.0.0.1:5173"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    # ===================
    # MongoDB Settings
    # ===================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "Skycart"
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 100

    # ===================
    # JWT Settings
    # ===================
    JWT_SECRET: str = Field(default="CHANGE_THIS_SECRET_IN_PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_EXPIRES_DAYS: int = 7

    # ===================
    # SMTP Settings
    # ===================
    SMTP_HOST: str = "smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM_NAME: str = "SkyCart"
    SMTP_FROM_EMAIL: str = "noreply@Skycart.com"
    SMTP_TLS: bool = True

    # ===================
    # Stripe Settings
    # ===================
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ===================
    # OAuth - Google
    # ===================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ===================
    # OAuth - GitHub
    # ===================
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # ===================
    # Kafka Settings
    # ===================
    KAFKA_ENABLED: bool = False
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = ""
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    KAFKA_PRODUCER_CLIENT_ID: str = "Skycart-producer"

    # ===================
    # Redis Settings
    # ===================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # ===================
    # File Storage Settings
    # ===================
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp"
    ]

    # ===================
    # Rate Limiting
    # ===================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # ===================
    # Logging Settings
    # ===================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # ===================
    # Pagination
    # ===================
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_IMAGE_TYPES", mode="before")
    @classmethod
    def parse_image_types(cls, v):
        """Parse image types from comma-separated string."""
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def mongodb_connection_string(self) -> str:
        """Get MongoDB connection string."""
        return self.MONGODB_URL

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Get CORS allowed origins."""
        return self.ALLOWED_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
