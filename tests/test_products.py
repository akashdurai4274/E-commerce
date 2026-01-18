"""
Product endpoint tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_products(client: AsyncClient):
    """Test getting products list."""
    response = await client.get("/api/v1/products")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "products" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_products_with_filters(client: AsyncClient):
    """Test getting products with filters."""
    response = await client.get(
        "/api/v1/products",
        params={
            "keyword": "laptop",
            "category": "Electronics",
            "page": 1,
            "resPerPage": 10
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_create_product_admin(admin_client: AsyncClient):
    """Test creating product as admin."""
    response = await admin_client.post(
        "/api/v1/products/admin/product/new",
        json={
            "name": "Test Product",
            "price": 99.99,
            "description": "A test product description",
            "category": "Electronics",
            "seller": "Test Seller",
            "stock": 100,
            "images": [{"image": "test.jpg"}]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"


@pytest.mark.asyncio
async def test_create_product_unauthorized(authenticated_client: AsyncClient):
    """Test that regular users cannot create products."""
    response = await authenticated_client.post(
        "/api/v1/products/admin/product/new",
        json={
            "name": "Test Product",
            "price": 99.99,
            "description": "A test product",
            "category": "Electronics",
            "seller": "Seller",
            "stock": 10
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    """Test getting non-existent product."""
    response = await client.get("/api/v1/products/000000000000000000000000")

    assert response.status_code == 404
