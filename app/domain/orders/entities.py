"""
Order domain entities.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import Field, field_validator, model_validator

from app.domain.shared.entity import BaseEntity
from app.domain.orders.value_objects import OrderStatus


class ShippingInfo(BaseEntity):
    """
    Shipping address information.

    Embedded within Order entity.
    """
    address: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, description="City")
    country: str = Field(..., min_length=1, description="Country")
    postal_code: str = Field(..., min_length=1, description="Postal/ZIP code")
    phone_no: str = Field(..., min_length=1, description="Contact phone number")


class PaymentInfo(BaseEntity):
    """
    Payment transaction information.

    Stores payment gateway response data.
    """
    id: str = Field(..., description="Payment gateway transaction ID")
    status: str = Field(..., description="Payment status from gateway")


class OrderItem(BaseEntity):
    """
    Individual item within an order.

    Contains snapshot of product at time of order.
    """
    product: str = Field(..., description="Product ID reference")
    name: str = Field(..., description="Product name at time of order")
    price: int = Field(..., ge=0, description="Price per unit")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    image: str = Field(..., description="Product image URL")

    @field_validator("price", mode="before")
    @classmethod
    def convert_price(cls, v):
        """Convert price to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal for this item."""
        return self.price * self.quantity


class Order(BaseEntity):
    """
    Order domain entity.

    Represents a customer order with all associated information
    including items, shipping, payment, and status.

    Business Rules:
    - Total price is calculated from items + tax + shipping
    - Status transitions follow defined state machine
    - Payment must be completed before shipping
    """

    user: str = Field(..., description="User ID who placed the order")
    shipping_info: ShippingInfo = Field(..., description="Shipping details")
    order_items: List[OrderItem] = Field(
        ...,
        min_length=1,
        description="Items in the order"
    )
    items_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Subtotal of all items"
    )
    tax_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Tax amount"
    )
    shipping_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Shipping cost"
    )
    total_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Total order amount"
    )
    payment_info: Optional[PaymentInfo] = Field(
        default=None,
        description="Payment details"
    )
    paid_at: Optional[datetime] = Field(
        default=None,
        description="Payment timestamp"
    )
    delivered_at: Optional[datetime] = Field(
        default=None,
        description="Delivery timestamp"
    )
    order_status: OrderStatus = Field(
        default=OrderStatus.PROCESSING,
        description="Current order status"
    )

    @field_validator("items_price", "tax_price", "shipping_price", "total_price", mode="before")
    @classmethod
    def convert_prices(cls, v):
        """Convert prices to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @model_validator(mode="after")
    def calculate_totals(self) -> "Order":
        """Calculate and validate order totals."""
        # Calculate items price from order items
        if self.order_items:
            self.items_price = sum(
                item.subtotal for item in self.order_items
            )

        # Calculate total
        self.total_price = (
            self.items_price +
            self.tax_price +
            self.shipping_price
        )

        return self

    def is_paid(self) -> bool:
        """Check if order has been paid."""
        return (
            self.payment_info is not None and
            self.payment_info.status == "succeeded"
        )

    def is_delivered(self) -> bool:
        """Check if order has been delivered."""
        return self.order_status == OrderStatus.DELIVERED

    def can_cancel(self) -> bool:
        """Check if order can be cancelled."""
        return self.order_status.is_cancellable()

    def can_transition_to(self, new_status: OrderStatus) -> bool:
        """Check if status can transition to new status."""
        return OrderStatus.can_transition_to(self.order_status, new_status)

    def update_status(self, new_status: OrderStatus) -> None:
        """
        Update order status with validation.

        Args:
            new_status: New status to set

        Raises:
            ValueError: If transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.order_status.value} "
                f"to {new_status.value}"
            )

        self.order_status = new_status

        if new_status == OrderStatus.DELIVERED:
            self.delivered_at = datetime.utcnow()

    def mark_as_paid(self, payment_id: str, payment_status: str) -> None:
        """
        Mark order as paid.

        Args:
            payment_id: Payment gateway transaction ID
            payment_status: Payment status from gateway
        """
        self.payment_info = PaymentInfo(id=payment_id, status=payment_status)
        self.paid_at = datetime.utcnow()

    def to_summary_dict(self) -> dict:
        """Get order summary for listing views."""
        return {
            "id": self.id,
            "user": self.user,
            "total_price": float(self.total_price),
            "order_status": self.order_status.value,
            "items_count": len(self.order_items),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
