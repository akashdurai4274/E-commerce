"""
Order request/response schemas.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.domain.orders.value_objects import OrderStatus


class ShippingInfoSchema(BaseModel):
    """Shipping information schema."""
    address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    country: str = Field(..., min_length=1)
    postal_code: str = Field(..., min_length=1)
    phone_no: str = Field(..., min_length=1)


class PaymentInfoSchema(BaseModel):
    """Payment information schema."""
    id: str
    status: str


class OrderItemSchema(BaseModel):
    """Order item schema."""
    product: str
    name: str
    price: float
    quantity: int = Field(..., ge=1)
    image: str


class OrderResponse(BaseModel):
    """Order data for API responses."""
    id: str
    user: str
    shipping_info: ShippingInfoSchema
    order_items: List[OrderItemSchema]
    items_price: float
    tax_price: float
    shipping_price: float
    total_price: float
    payment_info: Optional[PaymentInfoSchema] = None
    paid_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    order_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderCreateRequest(BaseModel):
    """Order creation request."""
    shipping_info: ShippingInfoSchema
    order_items: List[OrderItemSchema] = Field(..., min_length=1)
    items_price: Decimal = Field(..., ge=0)
    tax_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    shipping_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_info: PaymentInfoSchema


class OrderListResponse(BaseModel):
    """Paginated order list response."""
    success: bool = True
    count: int
    total: int
    page: int
    pages: int
    orders: List[OrderResponse]


class OrderStatusUpdateRequest(BaseModel):
    """Order status update request."""
    status: OrderStatus


class SalesStatsResponse(BaseModel):
    """Sales statistics response."""
    total_orders: int
    total_sales: float
    average_order_value: float
    delivered_orders: int
    processing_orders: int
    cancelled_orders: int
