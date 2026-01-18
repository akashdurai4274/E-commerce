"""
User repository interface.
Defines the contract for user data access operations.
"""
from abc import abstractmethod
from typing import Optional, List

from app.domain.shared.repository import BaseRepository
from app.domain.users.entities import User


class UserRepository(BaseRepository[User]):
    """
    User repository interface.

    Extends base repository with user-specific operations.
    """

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email address.

        Args:
            email: Email address to search for

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_reset_token(self, token_hash: str) -> Optional[User]:
        """
        Find a user by password reset token.

        Args:
            token_hash: Hashed reset token

        Returns:
            User if found with valid token, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_oauth(
        self,
        provider: str,
        provider_id: str
    ) -> Optional[User]:
        """
        Find a user by OAuth provider and provider user ID.

        Args:
            provider: OAuth provider name (google, github)
            provider_id: User ID from the OAuth provider

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        pass

    @abstractmethod
    async def update_password(
        self,
        user_id: str,
        hashed_password: str
    ) -> bool:
        """
        Update user's password.

        Args:
            user_id: User ID
            hashed_password: New hashed password

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def set_reset_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: "datetime"
    ) -> bool:
        """
        Set password reset token for a user.

        Args:
            user_id: User ID
            token_hash: Hashed reset token
            expires_at: Token expiration datetime

        Returns:
            True if set successfully
        """
        pass

    @abstractmethod
    async def clear_reset_token(self, user_id: str) -> bool:
        """
        Clear password reset token after use.

        Args:
            user_id: User ID

        Returns:
            True if cleared successfully
        """
        pass
