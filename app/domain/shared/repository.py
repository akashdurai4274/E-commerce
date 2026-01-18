"""
Base repository interface defining common data access operations.
Following the Repository pattern for Clean Architecture.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Tuple, Any

from app.domain.shared.entity import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository interface.

    Defines the contract for data access operations that all
    repository implementations must follow.

    Type Parameters:
        T: The entity type this repository manages
    """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the data store.

        Args:
            entity: Entity to create

        Returns:
            Created entity with assigned ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by its ID.

        Args:
            entity_id: Unique identifier

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: Entity with updated data

        Returns:
            Updated entity
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        Retrieve all entities with pagination.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def count(self, filter_query: dict | None = None) -> int:
        """
        Count entities matching the filter.

        Args:
            filter_query: Optional filter criteria

        Returns:
            Number of matching entities
        """
        pass

    @abstractmethod
    async def exists(self, filter_query: dict) -> bool:
        """
        Check if an entity matching the filter exists.

        Args:
            filter_query: Filter criteria

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def find_with_pagination(
        self,
        filter_query: dict | None = None,
        sort: List[Tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[T], int]:
        """
        Find entities with pagination and sorting.

        Args:
            filter_query: Optional filter criteria
            sort: List of (field, direction) tuples
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (entities list, total count)
        """
        pass
