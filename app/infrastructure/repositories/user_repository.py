"""
MongoDB User repository implementation.
"""
from typing import Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.repositories.base_mongo_repository import BaseMongoRepository
from app.domain.users.entities import User
from app.domain.users.repository import UserRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoUserRepository(BaseMongoRepository[User], UserRepository):
    """
    MongoDB implementation of User repository.

    Provides user-specific data access operations in addition to
    standard CRUD operations from base repository.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize user repository.

        Args:
            database: Motor async database instance
        """
        super().__init__(
            database=database,
            collection_name="users",
            entity_class=User
        )

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.

        Args:
            email: User's email

        Returns:
            User if found, None otherwise
        """
        document = await self._collection.find_one({"email": email.lower()})

        if document:
            logger.debug("User found by email", email=email)
            return self._to_entity(document)

        return None

    async def get_by_email_with_password(self, email: str) -> Optional[User]:
        """
        Find user by email including password field.

        Used for authentication where password verification is needed.

        Args:
            email: User's email

        Returns:
            User with password field if found
        """
        document = await self._collection.find_one({"email": email.lower()})

        if document:
            logger.debug("User found by email (with password)", email=email)
            return self._to_entity(document)

        return None

    async def get_by_reset_token(self, token: str) -> Optional[User]:
        """
        Find user by password reset token.

        Args:
            token: Hashed reset token

        Returns:
            User if found with valid token
        """
        document = await self._collection.find_one({
            "reset_password_token": token,
            "reset_password_token_expire": {"$gt": datetime.utcnow()}
        })

        if document:
            logger.debug("User found by reset token")
            return self._to_entity(document)

        return None

    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered.

        Args:
            email: Email to check

        Returns:
            True if email exists
        """
        return await self.exists({"email": email.lower()})
    
    async def clear_reset_token(self, user_id: str) -> bool:
        """
        Clear password reset token after use.

        Args:
            user_id: User ID

        Returns:
            True if cleared successfully
        """
        from bson import ObjectId

        result = await self._collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$unset": {
                    "reset_password_token": "",
                    "reset_password_token_expire": ""
                }
            }
        )

        logger.debug("Reset token cleared", user_id=user_id)
        return result.modified_count > 0


    async def get_by_oauth(
        self,
        provider: str,
        provider_id: str
    ) -> Optional[User]:
        """
        Find user by OAuth provider credentials.

        Args:
            provider: OAuth provider name (google, github, etc.)
            provider_id: User's ID from the OAuth provider

        Returns:
            User if found
        """
        document = await self._collection.find_one({
            "oauth_provider": provider,
            "oauth_provider_id": provider_id
        })

        if document:
            logger.debug(
                "User found by OAuth",
                provider=provider
            )
            return self._to_entity(document)

        return None

    async def update_avatar(self, user_id: str, avatar_url: str) -> bool:
        """
        Update user's avatar URL.

        Args:
            user_id: User ID
            avatar_url: New avatar URL

        Returns:
            True if updated successfully
        """
        from bson import ObjectId

        result = await self._collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"avatar": avatar_url}}
        )

        return result.modified_count > 0

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        """
        Update user's password.

        Args:
            user_id: User ID
            hashed_password: New hashed password

        Returns:
            True if updated successfully
        """
        from bson import ObjectId

        result = await self._collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password": hashed_password,
                    "reset_password_token": None,
                    "reset_password_token_expire": None
                }
            }
        )

        logger.debug("Password updated", user_id=user_id)
        return result.modified_count > 0

    async def set_reset_token(
        self,
        user_id: str,
        token: str,
        expire_at: datetime
    ) -> bool:
        """
        Set password reset token for user.

        Args:
            user_id: User ID
            token: Hashed reset token
            expire_at: Token expiration datetime

        Returns:
            True if updated successfully
        """
        from bson import ObjectId

        result = await self._collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "reset_password_token": token,
                    "reset_password_token_expire": expire_at
                }
            }
        )

        logger.debug("Reset token set", user_id=user_id)
        return result.modified_count > 0
