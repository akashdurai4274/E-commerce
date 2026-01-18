"""
MongoDB Product repository implementation.
"""
from typing import List, Tuple
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.repositories.base_mongo_repository import BaseMongoRepository
from app.domain.products.entities import Product
from app.domain.products.repository import ProductRepository
from app.domain.products.value_objects import ProductCategory
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoProductRepository(BaseMongoRepository[Product], ProductRepository):
    """
    MongoDB implementation of Product repository.

    Provides product-specific data access operations including
    full-text search, filtering, and review management.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize product repository.

        Args:
            database: Motor async database instance
        """
        super().__init__(
            database=database,
            collection_name="products",
            entity_class=Product
        )

    async def search(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Search products by keyword using text search.

        Uses MongoDB text index for efficient searching.
        """
        # Use regex for partial matching (text search requires full words)
        query = {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]
        }

        return await self.find_with_pagination(
            filter_query=query,
            sort=[("ratings", -1)],
            skip=skip,
            limit=limit
        )

    async def get_by_category(
        self,
        category: ProductCategory,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """Get products by category."""
        query = {"category": category.value}

        return await self.find_with_pagination(
            filter_query=query,
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def get_by_seller(
        self,
        seller: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """Get products by seller."""
        query = {"seller": {"$regex": seller, "$options": "i"}}

        return await self.find_with_pagination(
            filter_query=query,
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """Get products within a price range."""
        query = {
            "price": {
                "$gte": min_price,
                "$lte": max_price
            }
        }

        return await self.find_with_pagination(
            filter_query=query,
            sort=[("price", 1)],
            skip=skip,
            limit=limit
        )

    async def get_top_rated(self, limit: int = 10) -> List[Product]:
        """Get top-rated products."""
        return await self.find_many(
            filter_query={"ratings": {"$gt": 0}},
            sort=[("ratings", -1), ("num_of_reviews", -1)],
            skip=0,
            limit=limit
        )

    async def update_stock(
        self,
        product_id: str,
        quantity_change: int
    ) -> bool:
        """
        Update product stock atomically.

        Uses MongoDB $inc operator for atomic updates.
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return False

        result = await self._collection.update_one(
            {"_id": object_id, "stock": {"$gte": -quantity_change if quantity_change < 0 else 0}},
            {"$inc": {"stock": quantity_change}}
        )

        if result.modified_count > 0:
            logger.debug(
                "Stock updated",
                product_id=product_id,
                change=quantity_change
            )
            return True

        return False

    async def add_review(
        self,
        product_id: str,
        user_id: str,
        rating: float,
        comment: str
    ) -> bool:
        """
        Add or update a review for a product.

        If user already has a review, it will be updated.
        Recalculates average rating after adding review.
        """
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return False

        # First, try to update existing review
        result = await self._collection.update_one(
            {
                "_id": object_id,
                "reviews.user": user_id
            },
            {
                "$set": {
                    "reviews.$.rating": rating,
                    "reviews.$.comment": comment
                }
            }
        )

        if result.matched_count == 0:
            # No existing review, add new one
            review = {
                "_id": str(ObjectId()),
                "user": user_id,
                "rating": rating,
                "comment": comment,
                "created_at": datetime.utcnow()
            }

            result = await self._collection.update_one(
                {"_id": object_id},
                {
                    "$push": {"reviews": review},
                    "$inc": {"num_of_reviews": 1}
                }
            )

        # Recalculate average rating
        await self._recalculate_rating(product_id)

        logger.debug(
            "Review added/updated",
            product_id=product_id,
            user_id=user_id
        )

        return True

    async def remove_review(
        self,
        product_id: str,
        user_id: str
    ) -> bool:
        """Remove a user's review from a product."""
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return False

        result = await self._collection.update_one(
            {"_id": object_id},
            {
                "$pull": {"reviews": {"user": user_id}},
                "$inc": {"num_of_reviews": -1}
            }
        )

        if result.modified_count > 0:
            await self._recalculate_rating(product_id)
            logger.debug(
                "Review removed",
                product_id=product_id,
                user_id=user_id
            )
            return True

        return False

    async def _recalculate_rating(self, product_id: str) -> None:
        """Recalculate and update product's average rating."""
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return

        # Use aggregation to calculate average
        pipeline = [
            {"$match": {"_id": object_id}},
            {"$project": {
                "ratings": {
                    "$cond": {
                        "if": {"$eq": [{"$size": "$reviews"}, 0]},
                        "then": 0,
                        "else": {"$avg": "$reviews.rating"}
                    }
                }
            }}
        ]

        cursor = self._collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if result:
            new_rating = round(result[0].get("ratings", 0), 1)
            await self._collection.update_one(
                {"_id": object_id},
                {"$set": {"ratings": new_rating}}
            )

    async def get_admin_products(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """Get all products for admin panel."""
        return await self.find_with_pagination(
            filter_query={},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def filter_products(
        self,
        keyword: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        sort_by: str = "created_at",
        sort_order: int = -1,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Filter products with multiple criteria.

        This is the main method for product listing with filters.
        """
        query = {}

        # Keyword search
        if keyword:
            query["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]

        # Category filter
        if category:
            query["category"] = category

        # Price range
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price

        # Minimum rating
        if min_rating is not None:
            query["ratings"] = {"$gte": min_rating}

        return await self.find_with_pagination(
            filter_query=query,
            sort=[(sort_by, sort_order)],
            skip=skip,
            limit=limit
        )
