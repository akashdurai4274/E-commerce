"""
Order service.
Handles order management and processing.
"""
from typing import Optional, List, Tuple
from datetime import datetime
from decimal import Decimal

from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.core.logging import get_logger
from app.domain.orders.entities import Order, OrderItem, ShippingInfo, PaymentInfo
from app.domain.orders.value_objects import OrderStatus
from app.infrastructure.repositories.order_repository import MongoOrderRepository
from app.infrastructure.repositories.product_repository import MongoProductRepository

logger = get_logger(__name__)


class OrderService:
    """
    Order management service.

    Handles:
    - Order creation and processing
    - Order status management
    - Order queries
    - Stock management during orders
    """

    def __init__(
        self,
        order_repository: MongoOrderRepository,
        product_repository: MongoProductRepository
    ):
        """Initialize order service."""
        self._order_repo = order_repository
        self._product_repo = product_repository

    async def get_order(self, order_id: str) -> Order:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order entity

        Raises:
            NotFoundError: If order not found
        """
        order = await self._order_repo.get_by_id(order_id)

        if not order:
            raise NotFoundError("Order not found")

        return order

    async def get_user_order(self, order_id: str, user_id: str) -> Order:
        """
        Get order ensuring it belongs to user.

        Args:
            order_id: Order ID
            user_id: User ID

        Returns:
            Order entity

        Raises:
            NotFoundError: If order not found
            ForbiddenError: If order doesn't belong to user
        """
        order = await self.get_order(order_id)

        if order.user != user_id:
            raise ForbiddenError("Access denied")

        return order

    async def create_order(
        self,
        user_id: str,
        shipping_info: dict,
        order_items: List[dict],
        items_price: Decimal,
        tax_price: Decimal,
        shipping_price: Decimal,
        payment_info: dict
    ) -> Order:
        """
        Create a new order.

        Args:
            user_id: User placing the order
            shipping_info: Shipping address details
            order_items: List of items to order
            items_price: Subtotal
            tax_price: Tax amount
            shipping_price: Shipping cost
            payment_info: Payment details

        Returns:
            Created order

        Raises:
            ValidationError: If items unavailable
        """
        # Validate stock availability
        for item in order_items:
            product = await self._product_repo.get_by_id(item["product"])
            if not product:
                raise ValidationError(f"Product {item['product']} not found")
            if product.stock < item["quantity"]:
                raise ValidationError(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock}"
                )

        # Create order entities
        shipping = ShippingInfo(
            address=shipping_info["address"],
            city=shipping_info["city"],
            country=shipping_info["country"],
            postal_code=shipping_info["postal_code"],
            phone_no=shipping_info["phone_no"]
        )

        items = [
            OrderItem(
                product=item["product"],
                name=item["name"],
                price=Decimal(str(item["price"])),
                quantity=item["quantity"],
                image=item["image"]
            )
            for item in order_items
        ]

        payment = PaymentInfo(
            id=payment_info["id"],
            status=payment_info["status"]
        )

        order = Order(
            user=user_id,
            shipping_info=shipping,
            order_items=items,
            items_price=items_price,
            tax_price=tax_price,
            shipping_price=shipping_price,
            payment_info=payment,
            paid_at=datetime.utcnow() if payment_info["status"] == "succeeded" else None,
            order_status=OrderStatus.PROCESSING
        )

        # Create order
        created_order = await self._order_repo.create(order)

        # Reduce stock for each item
        for item in order_items:
            await self._product_repo.update_stock(
                item["product"],
                -item["quantity"]
            )

        logger.info(
            "Order created",
            order_id=created_order.id,
            user_id=user_id,
            total=float(created_order.total_price)
        )

        return created_order

    async def get_user_orders(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        """
        Get orders for a user.

        Args:
            user_id: User ID
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (orders, total)
        """
        skip = (page - 1) * limit
        return await self._order_repo.get_user_orders(user_id, skip, limit)

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus
    ) -> Order:
        """
        Update order status (admin).

        Args:
            order_id: Order ID
            status: New status

        Returns:
            Updated order

        Raises:
            ValidationError: If transition is invalid
        """
        order = await self.get_order(order_id)

        if not order.can_transition_to(status):
            raise ValidationError(
                f"Cannot transition from {order.order_status.value} "
                f"to {status.value}"
            )

        await self._order_repo.update_status(order_id, status)

        logger.info(
            "Order status updated",
            order_id=order_id,
            old_status=order.order_status.value,
            new_status=status.value
        )

        return await self.get_order(order_id)

    async def cancel_order(self, order_id: str, user_id: str) -> Order:
        """
        Cancel an order.

        Args:
            order_id: Order ID
            user_id: User ID (for verification)

        Returns:
            Cancelled order

        Raises:
            ValidationError: If order cannot be cancelled
        """
        order = await self.get_user_order(order_id, user_id)

        if not order.can_cancel():
            raise ValidationError("Order cannot be cancelled")

        # Restore stock
        for item in order.order_items:
            await self._product_repo.update_stock(
                item.product,
                item.quantity
            )

        await self._order_repo.update_status(order_id, OrderStatus.CANCELLED)

        logger.info("Order cancelled", order_id=order_id)

        return await self.get_order(order_id)

    async def get_all_orders(
        self,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Order], int]:
        """
        Get all orders (admin).

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (orders, total)
        """
        skip = (page - 1) * limit
        return await self._order_repo.find_with_pagination(
            filter_query={},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit
        )

    async def get_sales_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get sales statistics (admin).

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Sales statistics dict
        """
        return await self._order_repo.get_sales_stats(start_date, end_date)

    async def mark_as_delivered(self, order_id: str) -> Order:
        """
        Mark order as delivered (admin).

        Args:
            order_id: Order ID

        Returns:
            Updated order
        """
        order = await self.get_order(order_id)

        if not order.can_transition_to(OrderStatus.DELIVERED):
            raise ValidationError(
                f"Cannot mark as delivered from status {order.order_status.value}"
            )

        await self._order_repo.mark_as_delivered(order_id)

        logger.info("Order marked as delivered", order_id=order_id)

        return await self.get_order(order_id)
