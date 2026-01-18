"""
User service.
Handles user management operations.
"""
from typing import Optional, List, Tuple

from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger
from app.domain.users.entities import User
from app.domain.users.value_objects import UserRole
from app.infrastructure.repositories.user_repository import MongoUserRepository

logger = get_logger(__name__)


class UserService:
    """
    User management service.

    Handles:
    - User profile management
    - Admin user operations
    - User queries

    Design Notes:
    - Uses repository pattern for data access
    - Separates read/write operations
    - Validates business rules
    """

    def __init__(self, user_repository: MongoUserRepository):
        """Initialize user service."""
        self._user_repo = user_repository

    async def get_user_by_id(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User entity

        Raises:
            NotFoundError: If user not found
        """
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise NotFoundError("User not found")

        return user

    async def get_user_profile(self, user_id: str) -> dict:
        """
        Get user profile for API response.

        Args:
            user_id: User ID

        Returns:
            User profile dict (excludes sensitive data)
        """
        user = await self.get_user_by_id(user_id)
        return user.to_public_dict()

    async def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        avatar: Optional[str] = None
    ) -> User:
        """
        Update user profile.

        Args:
            user_id: User ID
            name: New name (optional)
            email: New email (optional)
            avatar: New avatar URL (optional)

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ConflictError: If new email already exists
        """
        user = await self.get_user_by_id(user_id)

        # Check email uniqueness if changing
        if email and email.lower() != user.email:
            if await self._user_repo.email_exists(email):
                raise ConflictError("Email already in use")
            user.email = email.lower()

        if name:
            user.name = name

        if avatar is not None:
            user.avatar = avatar

        updated_user = await self._user_repo.update(user)

        logger.info("User profile updated", user_id=user_id)

        return updated_user

    async def update_avatar(self, user_id: str, avatar_url: str) -> bool:
        """
        Update user's avatar.

        Args:
            user_id: User ID
            avatar_url: New avatar URL

        Returns:
            True if updated
        """
        success = await self._user_repo.update_avatar(user_id, avatar_url)

        if success:
            logger.info("Avatar updated", user_id=user_id)

        return success

    # Admin operations

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[User], int]:
        """
        Get all users (admin only).

        Args:
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (users, total count)
        """
        return await self._user_repo.find_with_pagination(
            filter_query={},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def admin_update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None
    ) -> User:
        """
        Admin update user.

        Args:
            user_id: User ID
            name: New name
            email: New email
            role: New role

        Returns:
            Updated user
        """
        user = await self.get_user_by_id(user_id)

        if name:
            user.name = name

        if email and email.lower() != user.email:
            if await self._user_repo.email_exists(email):
                raise ConflictError("Email already in use")
            user.email = email.lower()

        if role:
            user.role = UserRole(role)

        updated_user = await self._user_repo.update(user)

        logger.info(
            "Admin updated user",
            user_id=user_id,
            updated_fields={"name": name, "email": email, "role": role}
        )

        return updated_user

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user (admin only).

        Args:
            user_id: User ID

        Returns:
            True if deleted
        """
        # Verify user exists
        await self.get_user_by_id(user_id)

        success = await self._user_repo.delete(user_id)

        if success:
            logger.info("User deleted", user_id=user_id)

        return success
