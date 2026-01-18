"""
Domain layer containing business entities and repository interfaces.

The domain layer is the core of the application, containing:
- Entities: Business objects with identity and lifecycle
- Value Objects: Immutable objects representing domain concepts
- Repository Interfaces: Contracts for data persistence

This layer is independent of infrastructure concerns.
"""
from app.domain.users.entities import User
from app.domain.users.value_objects import UserRole
from app.domain.products.entities import Product, ProductImage, ProductReview
from app.domain.products.value_objects import ProductCategory
from app.domain.orders.entities import Order, OrderItem, ShippingInfo, PaymentInfo
from app.domain.orders.value_objects import OrderStatus
from app.domain.cart.entities import Cart, CartItem

__all__ = [
    # Users
    "User",
    "UserRole",
    # Products
    "Product",
    "ProductImage",
    "ProductReview",
    "ProductCategory",
    # Orders
    "Order",
    "OrderItem",
    "ShippingInfo",
    "PaymentInfo",
    "OrderStatus",
    # Cart
    "Cart",
    "CartItem",
]
