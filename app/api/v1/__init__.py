"""
API v1 router configuration.
Aggregates all domain routers into a single API router.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, products, orders, payments

api_router = APIRouter()

# Include all domain routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
