"""
Pydantic schemas for API request/response validation.
"""
from app.api.v1.schemas.common import PaginatedResponse, MessageResponse
from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.api.v1.schemas.users import (
    UserResponse,
    UserUpdateRequest,
    PasswordUpdateRequest,
)
from app.api.v1.schemas.products import (
    ProductResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductListResponse,
    ReviewCreateRequest,
)
from app.api.v1.schemas.orders import (
    OrderResponse,
    OrderCreateRequest,
    OrderListResponse,
    OrderStatusUpdateRequest,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "MessageResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    # Users
    "UserResponse",
    "UserUpdateRequest",
    "PasswordUpdateRequest",
    # Products
    "ProductResponse",
    "ProductCreateRequest",
    "ProductUpdateRequest",
    "ProductListResponse",
    "ReviewCreateRequest",
    # Orders
    "OrderResponse",
    "OrderCreateRequest",
    "OrderListResponse",
    "OrderStatusUpdateRequest",
]
