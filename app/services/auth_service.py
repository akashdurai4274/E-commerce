"""
Authentication service.
Handles user authentication, registration, and password management.
"""
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ConflictError,
)
from app.core.logging import get_logger
from app.domain.users.entities import User
from app.domain.users.value_objects import UserRole
from app.infrastructure.repositories.user_repository import MongoUserRepository

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service.

    Handles:
    - User registration
    - Login/logout
    - Password reset flow
    - JWT token management

    Design Notes:
    - Uses repository pattern for data access
    - Passwords are hashed using bcrypt
    - JWT tokens for stateless authentication
    """

    def __init__(self, user_repository: MongoUserRepository):
        """
        Initialize auth service.

        Args:
            user_repository: User repository instance
        """
        self._user_repo = user_repository

    async def register(
        self,
        name: str,
        email: str,
        password: str,
        avatar: Optional[str] = None
    ) -> tuple[User, str]:
        """
        Register a new user.

        Args:
            name: User's name
            email: User's email
            password: Plain text password
            avatar: Optional avatar URL

        Returns:
            Tuple of (created user, JWT token)

        Raises:
            ConflictError: If email already exists
        """
        # Check if email exists
        if await self._user_repo.email_exists(email):
            logger.warning("Registration failed: email exists", email=email)
            raise ConflictError("Email already registered")

        # Hash password
        hashed_password = hash_password(password)

        # Create user entity
        user = User(
            name=name,
            email=email.lower(),
            password=hashed_password,
            avatar=avatar,
            role=UserRole.USER
        )

        # Save to database
        created_user = await self._user_repo.create(user)

        # Generate token
        token = create_access_token({"sub": created_user.id})

        logger.info("User registered", user_id=created_user.id, email=email)

        return created_user, token

    async def login(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate user and return token.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            Tuple of (user, JWT token)

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        user = await self._user_repo.get_by_email_with_password(email)

        if not user:
            logger.warning("Login failed: user not found", email=email)
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not verify_password(password, user.password):
            logger.warning("Login failed: invalid password", email=email)
            raise AuthenticationError("Invalid email or password")

        # Generate token
        token = create_access_token({"sub": user.id})

        logger.info("User logged in", user_id=user.id)

        return user, token

    async def forgot_password(self, email: str) -> str:
        """
        Initiate password reset flow.

        Args:
            email: User's email

        Returns:
            Reset token (unhashed) to be sent via email

        Raises:
            NotFoundError: If user not found
        """
        user = await self._user_repo.get_by_email(email)

        if not user:
            # Don't reveal if email exists
            logger.warning("Password reset: user not found", email=email)
            raise NotFoundError("If this email exists, a reset link will be sent")

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()
        expire_at = datetime.utcnow() + timedelta(minutes=30)

        # Save token to user
        await self._user_repo.set_reset_token(
            user_id=user.id,
            token=hashed_token,
            expire_at=expire_at
        )

        logger.info("Password reset token generated", user_id=user.id)

        return reset_token

    async def reset_password(
        self,
        token: str,
        new_password: str
    ) -> User:
        """
        Reset password using token.

        Args:
            token: Reset token (unhashed)
            new_password: New password

        Returns:
            Updated user

        Raises:
            ValidationError: If token is invalid or expired
        """
        # Hash the token to match stored version
        hashed_token = hashlib.sha256(token.encode()).hexdigest()

        # Find user with valid token
        user = await self._user_repo.get_by_reset_token(hashed_token)

        if not user:
            logger.warning("Password reset failed: invalid token")
            raise ValidationError("Invalid or expired reset token")

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update password and clear token
        await self._user_repo.update_password(user.id, hashed_password)

        logger.info("Password reset successful", user_id=user.id)

        # Return updated user
        return await self._user_repo.get_by_id(user.id)

    async def get_current_user(self, token: str) -> User:
        """
        Get user from JWT token.

        Args:
            token: JWT token

        Returns:
            User entity

        Raises:
            AuthenticationError: If token is invalid
        """
        payload = decode_token(token)

        if not payload:
            raise AuthenticationError("Invalid token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise AuthenticationError("User not found")

        return user

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user's password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed

        Raises:
            AuthenticationError: If old password is incorrect
        """
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError("User not found")

        # Verify old password
        if not verify_password(old_password, user.password):
            raise AuthenticationError("Current password is incorrect")

        # Hash and update new password
        hashed_password = hash_password(new_password)
        await self._user_repo.update_password(user_id, hashed_password)

        logger.info("Password changed", user_id=user_id)

        return True
