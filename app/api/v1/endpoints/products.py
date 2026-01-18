"""
Product endpoints.
"""
from math import ceil
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query

from app.api.v1.dependencies import ProductServiceDep, CurrentUser, CurrentAdmin
from app.api.v1.schemas.products import (
    ProductResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductListResponse,
    ReviewCreateRequest,
    ProductImageSchema,
    ProductReviewSchema,
)
from app.api.v1.schemas.common import MessageResponse
from app.core.exceptions import NotFoundError

router = APIRouter()


def product_to_response(product) -> ProductResponse:
    """Convert product entity to response schema."""
    return ProductResponse(
        id=product.id,
        name=product.name,
        price=float(product.price),
        description=product.description,
        ratings=product.ratings,
        images=[ProductImageSchema(image=img.image) for img in product.images],
        category=product.category.value,
        seller=product.seller,
        stock=product.stock,
        num_of_reviews=product.num_of_reviews,
        reviews=[
            ProductReviewSchema(
                user=r.user,
                rating=r.rating,
                comment=r.comment
            )
            for r in product.reviews
        ],
        user=product.user,
        created_at=product.created_at
    )


@router.get("", response_model=ProductListResponse)
async def get_products(
    product_service: ProductServiceDep,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, alias="price[gte]", ge=0),
    max_price: Optional[float] = Query(None, alias="price[lte]", ge=0),
    min_rating: Optional[float] = Query(None, alias="ratings[gte]", ge=0, le=5),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100, alias="resPerPage")
):
    """
    Get products with filtering and pagination.

    Supports:
    - Keyword search in name and description
    - Category filter
    - Price range filter
    - Minimum rating filter
    - Pagination
    """
    products, total = await product_service.get_products(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        page=page,
        limit=limit
    )

    return ProductListResponse(
        count=len(products),
        total=total,
        page=page,
        pages=ceil(total / limit) if total > 0 else 1,
        results_per_page=limit,
        products=[product_to_response(p) for p in products]
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    product_service: ProductServiceDep
):
    """
    Get product by ID.
    """
    try:
        product = await product_service.get_product(product_id)
        return product_to_response(product)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{product_id}/review", response_model=MessageResponse)
async def create_review(
    product_id: str,
    request: ReviewCreateRequest,
    current_user: CurrentUser,
    product_service: ProductServiceDep
):
    """
    Create or update product review.

    Users can only have one review per product.
    Creating a new review updates the existing one.
    """
    try:
        await product_service.add_review(
            product_id=product_id,
            user_id=current_user.id,
            rating=request.rating,
            comment=request.comment
        )

        return MessageResponse(message="Review submitted successfully")

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{product_id}/review", response_model=MessageResponse)
async def delete_review(
    product_id: str,
    current_user: CurrentUser,
    product_service: ProductServiceDep
):
    """
    Delete user's review from product.
    """
    success = await product_service.delete_review(product_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    return MessageResponse(message="Review deleted successfully")


# Admin endpoints

@router.get("/admin/products", response_model=ProductListResponse)
async def get_admin_products(
    current_admin: CurrentAdmin,
    product_service: ProductServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get all products for admin.
    """
    products, total = await product_service.get_admin_products(page, limit)

    return ProductListResponse(
        count=len(products),
        total=total,
        page=page,
        pages=ceil(total / limit) if total > 0 else 1,
        results_per_page=limit,
        products=[product_to_response(p) for p in products]
    )


@router.post("/admin/product/new", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    current_admin: CurrentAdmin,
    product_service: ProductServiceDep
):
    """
    Create new product (admin only).
    """
    product = await product_service.create_product(
        name=request.name,
        price=request.price,
        description=request.description,
        category=request.category,
        seller=request.seller,
        stock=request.stock,
        images=[img.model_dump() for img in request.images],
        user_id=current_admin.id
    )

    return product_to_response(product)


@router.put("/admin/product/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    current_admin: CurrentAdmin,
    product_service: ProductServiceDep
):
    """
    Update product (admin only).
    """
    try:
        product = await product_service.update_product(
            product_id=product_id,
            name=request.name,
            price=request.price,
            description=request.description,
            category=request.category,
            seller=request.seller,
            stock=request.stock,
            images=[img.model_dump() for img in request.images] if request.images else None
        )

        return product_to_response(product)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/admin/product/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: str,
    current_admin: CurrentAdmin,
    product_service: ProductServiceDep
):
    """
    Delete product (admin only).
    """
    try:
        await product_service.delete_product(product_id)

        return MessageResponse(message="Product deleted successfully")

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
