"""
Base MongoDB repository implementation.
Provides common CRUD operations for all MongoDB collections.
"""
from typing import Generic, TypeVar, Optional, List, Tuple, Type, Any
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from app.domain.shared.entity import BaseEntity
from app.domain.shared.repository import BaseRepository
from app.core.logging import get_logger

T = TypeVar("T", bound=BaseEntity)

logger = get_logger(__name__)


class BaseMongoRepository(BaseRepository[T], Generic[T]):
    """
    Base MongoDB repository implementing common data access operations.

    This class provides a complete implementation of the BaseRepository interface
    using Motor (async MongoDB driver). It handles:
    - CRUD operations with proper async/await
    - ObjectId to string conversion
    - Pagination and filtering
    - Logging for all operations

    Type Parameters:
        T: The entity type this repository manages

    Architecture Notes:
        - Follows Repository pattern from Clean Architecture
        - Entity conversion happens at repository boundary
        - Uses dependency injection for database connection
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        collection_name: str,
        entity_class: Type[T]
    ):
        """
        Initialize repository with database connection.

        Args:
            database: Motor async database instance
            collection_name: Name of the MongoDB collection
            entity_class: Pydantic model class for deserialization
        """
        self._database = database
        self._collection_name = collection_name
        self._entity_class = entity_class
        self._collection: AsyncIOMotorCollection = database[collection_name]

    def _to_entity(self, document: dict) -> T:
        """
        Convert MongoDB document to domain entity.

        Handles ObjectId to string conversion for the _id field.

        Args:
            document: MongoDB document dict

        Returns:
            Domain entity instance
        """
        if document is None:
            return None

        # Convert ObjectId to string
        if "_id" in document and isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])

        # Convert any nested ObjectId fields
        document = self._convert_object_ids(document)

        return self._entity_class.model_validate(document)

    def _convert_object_ids(self, data: Any) -> Any:
        """
        Recursively convert ObjectId instances to strings.

        Args:
            data: Data to convert (dict, list, or primitive)

        Returns:
            Data with ObjectIds converted to strings
        """
        if isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, dict):
            return {k: self._convert_object_ids(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_object_ids(item) for item in data]
        return data

    def _to_document(self, entity: T) -> dict:
        """
        Convert domain entity to MongoDB document.

        Handles string to ObjectId conversion for the _id field.

        Args:
            entity: Domain entity

        Returns:
            MongoDB document dict
        """
        document = entity.model_dump(by_alias=True, exclude_none=True)

        # Convert string ID to ObjectId for MongoDB
        if "_id" in document and document["_id"]:
            document["_id"] = ObjectId(document["_id"])
        elif "_id" in document:
            del document["_id"]

        return document

    async def create(self, entity: T) -> T:
        """
        Create a new entity in MongoDB.

        Args:
            entity: Entity to create

        Returns:
            Created entity with assigned ID
        """
        document = self._to_document(entity)

        # Ensure created_at is set
        if "created_at" not in document:
            document["created_at"] = datetime.utcnow()

        result = await self._collection.insert_one(document)

        logger.debug(
            "Entity created",
            collection=self._collection_name,
            id=str(result.inserted_id)
        )

        # Fetch and return the created document
        created_doc = await self._collection.find_one({"_id": result.inserted_id})
        return self._to_entity(created_doc)

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by its ID.

        Args:
            entity_id: MongoDB ObjectId as string

        Returns:
            Entity if found, None otherwise
        """
        try:
            object_id = ObjectId(entity_id)
        except Exception:
            logger.warning(
                "Invalid ObjectId format",
                collection=self._collection_name,
                id=entity_id
            )
            return None

        document = await self._collection.find_one({"_id": object_id})

        if document:
            logger.debug(
                "Entity retrieved",
                collection=self._collection_name,
                id=entity_id
            )
            return self._to_entity(document)

        return None

    async def update(self, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            entity: Entity with updated data

        Returns:
            Updated entity

        Raises:
            ValueError: If entity has no ID
        """
        if not entity.id:
            raise ValueError("Cannot update entity without ID")

        document = self._to_document(entity)
        object_id = ObjectId(entity.id)

        # Remove _id from update data
        update_data = {k: v for k, v in document.items() if k != "_id"}

        result = await self._collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

        logger.debug(
            "Entity updated",
            collection=self._collection_name,
            id=entity.id,
            modified_count=result.modified_count
        )

        # Fetch and return updated document
        updated_doc = await self._collection.find_one({"_id": object_id})
        return self._to_entity(updated_doc)

    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            object_id = ObjectId(entity_id)
        except Exception:
            return False

        result = await self._collection.delete_one({"_id": object_id})

        logger.debug(
            "Entity deleted",
            collection=self._collection_name,
            id=entity_id,
            deleted_count=result.deleted_count
        )

        return result.deleted_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Retrieve all entities with pagination.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        cursor = self._collection.find().skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)

        logger.debug(
            "Entities retrieved",
            collection=self._collection_name,
            count=len(documents),
            skip=skip,
            limit=limit
        )

        return [self._to_entity(doc) for doc in documents]

    async def count(self, filter_query: dict | None = None) -> int:
        """
        Count entities matching the filter.

        Args:
            filter_query: Optional filter criteria

        Returns:
            Number of matching entities
        """
        query = filter_query or {}
        count = await self._collection.count_documents(query)

        logger.debug(
            "Entity count",
            collection=self._collection_name,
            count=count,
            filter=query
        )

        return count

    async def exists(self, filter_query: dict) -> bool:
        """
        Check if an entity matching the filter exists.

        Args:
            filter_query: Filter criteria

        Returns:
            True if exists, False otherwise
        """
        document = await self._collection.find_one(filter_query)
        return document is not None

    async def find_one(self, filter_query: dict) -> Optional[T]:
        """
        Find a single entity matching the filter.

        Args:
            filter_query: Filter criteria

        Returns:
            Entity if found, None otherwise
        """
        document = await self._collection.find_one(filter_query)

        if document:
            return self._to_entity(document)

        return None

    async def find_many(
        self,
        filter_query: dict | None = None,
        sort: List[Tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        Find multiple entities with optional filtering and sorting.

        Args:
            filter_query: Optional filter criteria
            sort: List of (field, direction) tuples (1 for asc, -1 for desc)
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of matching entities
        """
        query = filter_query or {}
        cursor = self._collection.find(query)

        if sort:
            cursor = cursor.sort(sort)

        cursor = cursor.skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)

        return [self._to_entity(doc) for doc in documents]

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
        query = filter_query or {}

        # Get total count for pagination
        total = await self._collection.count_documents(query)

        # Get paginated results
        entities = await self.find_many(
            filter_query=query,
            sort=sort,
            skip=skip,
            limit=limit
        )

        logger.debug(
            "Paginated query executed",
            collection=self._collection_name,
            total=total,
            returned=len(entities),
            skip=skip,
            limit=limit
        )

        return entities, total

    async def aggregate(self, pipeline: List[dict]) -> List[dict]:
        """
        Execute an aggregation pipeline.

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            List of aggregation results
        """
        cursor = self._collection.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def update_many(
        self,
        filter_query: dict,
        update_data: dict
    ) -> int:
        """
        Update multiple documents matching the filter.

        Args:
            filter_query: Filter criteria
            update_data: Update operations

        Returns:
            Number of modified documents
        """
        result = await self._collection.update_many(
            filter_query,
            {"$set": update_data}
        )

        logger.debug(
            "Bulk update executed",
            collection=self._collection_name,
            matched=result.matched_count,
            modified=result.modified_count
        )

        return result.modified_count

    async def delete_many(self, filter_query: dict) -> int:
        """
        Delete multiple documents matching the filter.

        Args:
            filter_query: Filter criteria

        Returns:
            Number of deleted documents
        """
        result = await self._collection.delete_many(filter_query)

        logger.debug(
            "Bulk delete executed",
            collection=self._collection_name,
            deleted=result.deleted_count
        )

        return result.deleted_count
