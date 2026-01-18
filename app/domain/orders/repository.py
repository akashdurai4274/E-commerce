"""
Order repository interface.
"""
from abc import abstractmethod
from typing import List, Tuple, Optional
from datetime import datetime

from app.domain.shared.repository import BaseRepository
from app.domain.orders.entities import Order
from app.domain.orders.value_objects import OrderStatus


class OrderRepository(BaseRepository[Order]):
    """
    Order repository interface.

    Extends base repository with order-specific operations.
    """

    @abstractmethod
    async def get_user_orders(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        """
        Get orders for a specific user.

        Args:
            user_id: User ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (orders, total count)
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: OrderStatus,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        """
        Get orders by status.

        Args:
            status: Order status to filter by
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (orders, total count)
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        order_id: str,
        status: OrderStatus
    ) -> bool:
        """
        Update order status.

        Args:
            order_id: Order ID
            status: New status

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def mark_as_delivered(
        self,
        order_id: str,
        delivered_at: Optional[datetime] = None
    ) -> bool:
        """
        Mark order as delivered.

        Args:
            order_id: Order ID
            delivered_at: Delivery timestamp (defaults to now)

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def get_sales_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get sales statistics.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Dict with sales statistics
        """
        pass

    @abstractmethod
    async def get_recent_orders(
        self,
        limit: int = 10
    ) -> List[Order]:
        """
        Get most recent orders.

        Args:
            limit: Maximum to return

        Returns:
            List of recent orders
        """
        pass
