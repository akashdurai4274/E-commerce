"""
Cart domain entities.
Cart is primarily managed client-side but we define entities
for API validation and order creation.
"""
from typing import List
from decimal import Decimal
from pydantic import Field, field_validator

from app.domain.shared.entity import BaseEntity


class CartItem(BaseEntity):
    """
    Individual item in shopping cart.

    Used for validating cart data when creating orders.
    """
    product: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: Decimal = Field(..., ge=0, description="Unit price")
    quantity: int = Field(..., ge=1, description="Quantity")
    image: str = Field(..., description="Product image URL")
    stock: int = Field(..., ge=0, description="Available stock")

    @field_validator("price", mode="before")
    @classmethod
    def convert_price(cls, v):
        """Convert price to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @property
    def subtotal(self) -> Decimal:
        """Calculate item subtotal."""
        return self.price * self.quantity

    def can_add_more(self, additional: int = 1) -> bool:
        """Check if more items can be added."""
        return (self.quantity + additional) <= self.stock


class Cart(BaseEntity):
    """
    Shopping cart.

    Primarily used for validation when processing checkout.
    """
    items: List[CartItem] = Field(default_factory=list)

    @property
    def items_count(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self) -> Decimal:
        """Calculate cart subtotal."""
        return sum(item.subtotal for item in self.items)

    def add_item(self, item: CartItem) -> None:
        """Add item to cart or update quantity if exists."""
        for existing in self.items:
            if existing.product == item.product:
                existing.quantity += item.quantity
                return
        self.items.append(item)

    def remove_item(self, product_id: str) -> bool:
        """Remove item from cart."""
        initial_count = len(self.items)
        self.items = [i for i in self.items if i.product != product_id]
        return len(self.items) < initial_count

    def update_quantity(self, product_id: str, quantity: int) -> bool:
        """Update item quantity."""
        for item in self.items:
            if item.product == product_id:
                if quantity <= 0:
                    return self.remove_item(product_id)
                item.quantity = quantity
                return True
        return False

    def clear(self) -> None:
        """Clear all items from cart."""
        self.items = []

    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.items) == 0
