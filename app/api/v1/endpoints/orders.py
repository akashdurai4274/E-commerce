"""
Order endpoints.
"""
from math import ceil
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query

from app.api.v1.dependencies import OrderServiceDep, CurrentUser, CurrentAdmin
from app.api.v1.schemas.orders import (
    OrderResponse,
    OrderCreateRequest,
    OrderListResponse,
    OrderStatusUpdateRequest,
    ShippingInfoSchema,
    PaymentInfoSchema,
    OrderItemSchema,
    SalesStatsResponse,
)
from app.api.v1.schemas.common import MessageResponse
from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError

router = APIRouter()


def order_to_response(order) -> OrderResponse:
    """Convert order entity to response schema."""
    return OrderResponse(
        id=order.id,
        user=order.user,
        shipping_info=ShippingInfoSchema(
            address=order.shipping_info.address,
            city=order.shipping_info.city,
            country=order.shipping_info.country,
            postal_code=order.shipping_info.postal_code,
            phone_no=order.shipping_info.phone_no
        ),
        order_items=[
            OrderItemSchema(
                product=item.product,
                name=item.name,
                price=float(item.price),
                quantity=item.quantity,
                image=item.image
            )
            for item in order.order_items
        ],
        items_price=float(order.items_price),
        tax_price=float(order.tax_price),
        shipping_price=float(order.shipping_price),
        total_price=float(order.total_price),
        payment_info=PaymentInfoSchema(
            id=order.payment_info.id,
            status=order.payment_info.status
        ) if order.payment_info else None,
        paid_at=order.paid_at,
        delivered_at=order.delivered_at,
        order_status=order.order_status.value,
        created_at=order.created_at
    )


@router.post("/new", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    current_user: CurrentUser,
    order_service: OrderServiceDep
):
    """
    Create a new order.

    Validates stock availability and reduces stock on success.
    """
    try:
        order = await order_service.create_order(
            user_id=current_user.id,
            shipping_info=request.shipping_info.model_dump(),
            order_items=[item.model_dump() for item in request.order_items],
            items_price=request.items_price,
            tax_price=request.tax_price,
            shipping_price=request.shipping_price,
            payment_info=request.payment_info.model_dump()
        )

        return order_to_response(order)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=OrderListResponse)
async def get_my_orders(
    current_user: CurrentUser,
    order_service: OrderServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get current user's orders.
    """
    orders, total = await order_service.get_user_orders(
        user_id=current_user.id,
        page=page,
        limit=limit
    )

    return OrderListResponse(
        count=len(orders),
        total=total,
        page=page,
        pages=ceil(total / limit) if total > 0 else 1,
        orders=[order_to_response(o) for o in orders]
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: CurrentUser,
    order_service: OrderServiceDep
):
    """
    Get order by ID.

    Users can only access their own orders.
    """
    try:
        order = await order_service.get_user_order(order_id, current_user.id)
        return order_to_response(order)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    current_user: CurrentUser,
    order_service: OrderServiceDep
):
    """
    Cancel an order.

    Only orders in Processing, Confirmed, or Shipped status can be cancelled.
    """
    try:
        order = await order_service.cancel_order(order_id, current_user.id)
        return order_to_response(order)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Admin endpoints

@router.get("/admin/orders", response_model=OrderListResponse)
async def get_all_orders(
    current_admin: CurrentAdmin,
    order_service: OrderServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get all orders (admin only).
    """
    orders, total = await order_service.get_all_orders(page, limit)

    return OrderListResponse(
        count=len(orders),
        total=total,
        page=page,
        pages=ceil(total / limit) if total > 0 else 1,
        orders=[order_to_response(o) for o in orders]
    )


@router.get("/admin/order/{order_id}", response_model=OrderResponse)
async def admin_get_order(
    order_id: str,
    current_admin: CurrentAdmin,
    order_service: OrderServiceDep
):
    """
    Get order by ID (admin only).
    """
    try:
        order = await order_service.get_order(order_id)
        return order_to_response(order)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/admin/order/{order_id}", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    request: OrderStatusUpdateRequest,
    current_admin: CurrentAdmin,
    order_service: OrderServiceDep
):
    """
    Update order status (admin only).
    """
    try:
        order = await order_service.update_order_status(order_id, request.status)
        return order_to_response(order)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/admin/order/{order_id}/deliver", response_model=OrderResponse)
async def mark_order_delivered(
    order_id: str,
    current_admin: CurrentAdmin,
    order_service: OrderServiceDep
):
    """
    Mark order as delivered (admin only).
    """
    try:
        order = await order_service.mark_as_delivered(order_id)
        return order_to_response(order)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/admin/stats", response_model=SalesStatsResponse)
async def get_sales_stats(
    current_admin: CurrentAdmin,
    order_service: OrderServiceDep,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get sales statistics (admin only).
    """
    stats = await order_service.get_sales_stats(start_date, end_date)

    return SalesStatsResponse(
        total_orders=stats["total_orders"],
        total_sales=float(stats.get("total_sales", 0)),
        average_order_value=float(stats.get("average_order_value", 0)),
        delivered_orders=stats.get("delivered_orders", 0),
        processing_orders=stats.get("processing_orders", 0),
        cancelled_orders=stats.get("cancelled_orders", 0)
    )
