"""
API dependencies for dependency injection.
Provides service instances and authentication.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_database
from app.core.security import decode_token
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.domain.users.entities import User
from app.domain.users.value_objects import UserRole
from app.infrastructure.repositories.user_repository import MongoUserRepository
from app.infrastructure.repositories.product_repository import MongoProductRepository
from app.infrastructure.repositories.order_repository import MongoOrderRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

# Security scheme
security = HTTPBearer()


# Repository dependencies
async def get_user_repository(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> MongoUserRepository:
    """Get user repository instance."""
    return MongoUserRepository(db)


async def get_product_repository(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> MongoProductRepository:
    """Get product repository instance."""
    return MongoProductRepository(db)


async def get_order_repository(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> MongoOrderRepository:
    """Get order repository instance."""
    return MongoOrderRepository(db)


# Service dependencies
async def get_auth_service(
    user_repo: MongoUserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repo)


async def get_user_service(
    user_repo: MongoUserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service instance."""
    return UserService(user_repo)


async def get_product_service(
    product_repo: MongoProductRepository = Depends(get_product_repository)
) -> ProductService:
    """Get product service instance."""
    return ProductService(product_repo)


async def get_order_service(
    order_repo: MongoOrderRepository = Depends(get_order_repository),
    product_repo: MongoProductRepository = Depends(get_product_repository)
) -> OrderService:
    """Get order service instance."""
    return OrderService(order_repo, product_repo)


async def get_payment_service() -> PaymentService:
    """Get payment service instance."""
    return PaymentService()


# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user.

    Extracts JWT from Authorization header and returns user.
    """
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_admin(
    user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify admin role.

    Raises 403 if user is not admin.
    """
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Type aliases for cleaner annotations
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
