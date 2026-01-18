"""
Value objects for the User domain.
Immutable objects that represent domain concepts.
"""
from enum import Enum


class UserRole(str, Enum):
    """
    User role enumeration.

    Defines the roles a user can have in the system.
    """
    USER = "user"
    ADMIN = "admin"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "UserRole":
        """Create UserRole from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.USER  # Default to user role
