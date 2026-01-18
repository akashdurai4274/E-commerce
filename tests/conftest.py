"""
Pytest configuration and fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing.

    Yields:
        AsyncClient configured for testing
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator:
    """
    Create test database connection.

    Uses a separate test database that is cleaned after each test.
    """
    # Use test database
    test_db_name = f"{settings.MONGODB_DB_NAME}_test"
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[test_db_name]

    yield db

    # Cleanup: drop all collections after test
    collections = await db.list_collection_names()
    for collection in collections:
        await db.drop_collection(collection)

    client.close()


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """
    Create authenticated client for protected endpoints.

    Registers a test user and returns client with auth token.
    """
    # Register test user
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    token = response.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"

    return client


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, test_db) -> AsyncClient:
    """
    Create admin authenticated client.

    Creates an admin user directly in database.
    """
    from app.core.security import hash_password

    # Create admin user directly
    await test_db.users.insert_one({
        "name": "Admin User",
        "email": "admin@example.com",
        "password": hash_password("admin123"),
        "role": "admin"
    })

    # Login as admin
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123"
        }
    )

    token = response.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"

    return client
