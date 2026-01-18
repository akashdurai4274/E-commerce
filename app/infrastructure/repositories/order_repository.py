"""
MongoDB Order repository implementation.
"""
from typing import List, Tuple, Optional
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.infrastructure.repositories.base_mongo_repository import BaseMongoRepository
from app.domain.orders.entities import Order
from app.domain.orders.repository import OrderRepository
from app.domain.orders.value_objects import OrderStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoOrderRepository(BaseMongoRepository[Order], OrderRepository):
    """
    MongoDB implementation of Order repository.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """Initialize order repository."""
        super().__init__(
            database=database,
            collection_name="orders",
            entity_class=Order
        )

    async def get_user_orders(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        """Get orders for a specific user."""
        query = {"user": user_id}

        return await self.find_with_pagination(
            filter_query=query,
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def get_by_status(
        self,
        status: OrderStatus,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        """Get orders by status."""
        query = {"order_status": status.value}

        return await self.find_with_pagination(
            filter_query=query,
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def update_status(
        self,
        order_id: str,
        status: OrderStatus
    ) -> bool:
        """Update order status."""
        try:
            object_id = ObjectId(order_id)
        except Exception:
            return False

        update_data = {"order_status": status.value}

        if status == OrderStatus.DELIVERED:
            update_data["delivered_at"] = datetime.utcnow()

        result = await self._collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            logger.debug(
                "Order status updated",
                order_id=order_id,
                status=status.value
            )
            return True

        return False

    async def mark_as_delivered(
        self,
        order_id: str,
        delivered_at: Optional[datetime] = None
    ) -> bool:
        """Mark order as delivered."""
        try:
            object_id = ObjectId(order_id)
        except Exception:
            return False

        result = await self._collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "order_status": OrderStatus.DELIVERED.value,
                    "delivered_at": delivered_at or datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    async def get_sales_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get sales statistics using aggregation pipeline.

        Returns total orders, total sales amount, and breakdown by status.
        """
        match_stage = {}

        if start_date or end_date:
            match_stage["created_at"] = {}
            if start_date:
                match_stage["created_at"]["$gte"] = start_date
            if end_date:
                match_stage["created_at"]["$lte"] = end_date

        pipeline = []

        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.extend([
            {
                "$group": {
                    "_id": None,
                    "total_orders": {"$sum": 1},
                    "total_sales": {"$sum": "$total_price"},
                    "average_order_value": {"$avg": "$total_price"},
                    "delivered_orders": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$order_status", OrderStatus.DELIVERED.value]},
                                1, 0
                            ]
                        }
                    },
                    "processing_orders": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$order_status", OrderStatus.PROCESSING.value]},
                                1, 0
                            ]
                        }
                    },
                    "cancelled_orders": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$order_status", OrderStatus.CANCELLED.value]},
                                1, 0
                            ]
                        }
                    }
                }
            }
        ])

        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)

        if results:
            stats = results[0]
            del stats["_id"]
            return stats

        return {
            "total_orders": 0,
            "total_sales": 0,
            "average_order_value": 0,
            "delivered_orders": 0,
            "processing_orders": 0,
            "cancelled_orders": 0
        }

    async def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get most recent orders."""
        return await self.find_many(
            filter_query={},
            sort=[("created_at", -1)],
            skip=0,
            limit=limit
        )

    async def get_daily_sales(
        self,
        days: int = 30
    ) -> List[dict]:
        """
        Get daily sales data for the last N days.

        Useful for dashboard charts.
        """
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date},
                    "order_status": {"$ne": OrderStatus.CANCELLED.value}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "orders": {"$sum": 1},
                    "sales": {"$sum": "$total_price"}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        cursor = self._collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
