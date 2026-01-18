"""
Base entity class for all domain entities.
Provides common functionality and ID handling.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BaseEntity(BaseModel):
    """
    Base class for all domain entities.

    Provides:
    - MongoDB ObjectId as string ID
    - Created timestamp
    - Pydantic model configuration
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __eq__(self, other: object) -> bool:
        """Two entities are equal if they have the same ID."""
        if not isinstance(other, BaseEntity):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id) if self.id else hash(id(self))
