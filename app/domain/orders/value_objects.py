"""
Order domain value objects.
"""
from enum import Enum


class OrderStatus(str, Enum):
    """
    Order lifecycle status.

    Represents the various stages an order goes through
    from creation to delivery.
    """
    PROCESSING = "Processing"
    CONFIRMED = "Confirmed"
    SHIPPED = "Shipped"
    OUT_FOR_DELIVERY = "Out for Delivery"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"

    @classmethod
    def can_transition_to(cls, current: "OrderStatus", new: "OrderStatus") -> bool:
        """
        Check if status transition is valid.

        Defines the valid state machine for order status changes.
        """
        valid_transitions = {
            cls.PROCESSING: [cls.CONFIRMED, cls.CANCELLED],
            cls.CONFIRMED: [cls.SHIPPED, cls.CANCELLED],
            cls.SHIPPED: [cls.OUT_FOR_DELIVERY, cls.CANCELLED],
            cls.OUT_FOR_DELIVERY: [cls.DELIVERED],
            cls.DELIVERED: [cls.REFUNDED],
            cls.CANCELLED: [],
            cls.REFUNDED: [],
        }

        return new in valid_transitions.get(current, [])

    def is_final(self) -> bool:
        """Check if this is a final status (no more transitions allowed)."""
        return self in [self.DELIVERED, self.CANCELLED, self.REFUNDED]

    def is_cancellable(self) -> bool:
        """Check if order with this status can be cancelled."""
        return self in [self.PROCESSING, self.CONFIRMED, self.SHIPPED]


class PaymentStatus(str, Enum):
    """Payment status for orders."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
