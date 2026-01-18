"""
Product request/response schemas.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.domain.products.value_objects import ProductCategory


class ProductImageSchema(BaseModel):
    """Product image schema."""
    image: str


class ProductReviewSchema(BaseModel):
    """Product review schema."""
    user: str
    rating: float = Field(..., ge=0, le=5)
    comment: str


class ProductResponse(BaseModel):
    """Product data for API responses."""
    id: str
    name: str
    price: int
    description: str
    ratings: float
    images: List[ProductImageSchema]
    category: str
    seller: str
    stock: int
    num_of_reviews: int
    reviews: List[ProductReviewSchema]
    user: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductCreateRequest(BaseModel):
    """Product creation request."""
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., ge=0)
    description: str = Field(..., min_length=1)
    category: ProductCategory
    seller: str = Field(..., min_length=1)
    stock: int = Field(..., ge=0)
    images: List[ProductImageSchema] = Field(default_factory=list)


class ProductUpdateRequest(BaseModel):
    """Product update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    seller: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    images: Optional[List[ProductImageSchema]] = None


class ProductListResponse(BaseModel):
    """Paginated product list response."""
    success: bool = True
    count: int
    total: int
    page: int
    pages: int
    results_per_page: int
    products: List[ProductResponse]


class ReviewCreateRequest(BaseModel):
    """Create product review request."""
    rating: float = Field(..., ge=0, le=5)
    comment: str = Field(..., min_length=1)


class ProductFilterParams(BaseModel):
    """Product filter query parameters."""
    keyword: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
