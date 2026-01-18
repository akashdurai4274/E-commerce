"""
User domain entity.
Represents a user in the system with all business rules.
"""
from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr

from app.domain.shared.entity import BaseEntity
from app.domain.users.value_objects import UserRole


class User(BaseEntity):
    """
    User domain entity.

    Contains all user data and business rules related to users.
    """

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    avatar: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)
    reset_password_token: Optional[str] = None
    reset_password_token_expire: Optional[datetime] = None

    # OAuth fields
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN

    def can_reset_password(self) -> bool:
        """Check if password reset token is valid."""
        if not self.reset_password_token:
            return False
        if not self.reset_password_token_expire:
            return False
        return datetime.utcnow() < self.reset_password_token_expire

    def clear_reset_token(self) -> None:
        """Clear password reset token after use."""
        self.reset_password_token = None
        self.reset_password_token_expire = None

    def is_oauth_user(self) -> bool:
        """Check if user registered via OAuth."""
        return self.oauth_provider is not None

    def to_public_dict(self) -> dict:
        """
        Convert to dictionary excluding sensitive fields.

        Used for API responses.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "avatar": self.avatar,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
