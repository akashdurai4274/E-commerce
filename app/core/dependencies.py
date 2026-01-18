"""
Global dependency injection for FastAPI.
Provides database connections and other shared resources.
"""
from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global MongoDB client instance
_mongo_client: Optional[AsyncIOMotorClient] = None


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Get MongoDB database instance.

    This is a FastAPI dependency that provides access to the database.
    The connection is reused across requests for efficiency.

    Yields:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    global _mongo_client

    if _mongo_client is None:
        logger.info(
            "Creating MongoDB connection",
            url=settings.MONGODB_URL,
            db=settings.MONGODB_DB_NAME
        )
        _mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE
        )

    yield _mongo_client[settings.MONGODB_DB_NAME]


async def init_database() -> None:
    """
    Initialize database connection and create indexes.

    Called during application startup.
    """
    global _mongo_client

    if _mongo_client is None:
        logger.info(
            "Initializing MongoDB connection",
            url=settings.MONGODB_URL,
            db=settings.MONGODB_DB_NAME
        )
        _mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE
        )

    db = _mongo_client[settings.MONGODB_DB_NAME]

    # Create indexes for users collection
    await db.users.create_index("email", unique=True)
    await db.users.create_index("reset_password_token")

    # Create indexes for products collection
    await db.products.create_index("name")
    await db.products.create_index("category")
    await db.products.create_index("price")
    await db.products.create_index("ratings")
    await db.products.create_index([("name", "text"), ("description", "text")])

    # Create indexes for orders collection
    await db.orders.create_index("user")
    await db.orders.create_index("created_at")
    await db.orders.create_index("order_status")

    logger.info("Database indexes created successfully")


async def close_database() -> None:
    """
    Close database connection.

    Called during application shutdown.
    """
    global _mongo_client

    if _mongo_client is not None:
        logger.info("Closing MongoDB connection")
        _mongo_client.close()
        _mongo_client = None


def get_mongo_client() -> Optional[AsyncIOMotorClient]:
    """
    Get the MongoDB client instance.

    Returns:
        MongoDB client or None if not initialized
    """
    return _mongo_client
