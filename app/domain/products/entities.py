"""
Product domain entities.
Represents products in the e-commerce system.
"""
from typing import Optional, List
from decimal import Decimal
from pydantic import Field, field_validator

from app.domain.shared.entity import BaseEntity
from app.domain.products.value_objects import ProductCategory


class ProductImage(BaseEntity):
    """
    Represents a product image.

    Stored as embedded document within Product.
    """
    image: str = Field(..., description="Image URL or path")


class ProductReview(BaseEntity):
    """
    Represents a customer review for a product.

    Stored as embedded document within Product.
    """
    user: str = Field(..., description="User ID who wrote the review")
    rating: float = Field(..., ge=0, le=5, description="Rating from 0-5")
    comment: str = Field(..., min_length=1, description="Review comment")

    @field_validator("rating", mode="before")
    @classmethod
    def convert_rating(cls, v):
        """Convert string ratings to float."""
        if isinstance(v, str):
            return float(v)
        return v


class Product(BaseEntity):
    """
    Product domain entity.

    Represents a product available for purchase in the e-commerce platform.
    Contains all product information including pricing, inventory, and reviews.

    Business Rules:
    - Stock cannot be negative
    - Price must be non-negative
    - Rating is calculated from reviews
    - Category must be from predefined list
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product name"
    )
    price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Product price"
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Product description"
    )
    ratings: float = Field(
        default=0.0,
        ge=0,
        le=5,
        description="Average product rating"
    )
    images: List[ProductImage] = Field(
        default_factory=list,
        description="Product images"
    )
    category: ProductCategory = Field(
        ...,
        description="Product category"
    )
    seller: str = Field(
        ...,
        min_length=1,
        description="Seller/Brand name"
    )
    stock: int = Field(
        ...,
        ge=0,
        description="Available stock quantity"
    )
    num_of_reviews: int = Field(
        default=0,
        ge=0,
        description="Number of reviews"
    )
    reviews: List[ProductReview] = Field(
        default_factory=list,
        description="Product reviews"
    )
    user: Optional[str] = Field(
        default=None,
        description="ID of user who created the product"
    )

    @field_validator("ratings", mode="before")
    @classmethod
    def convert_ratings(cls, v):
        """Convert string ratings to float."""
        if isinstance(v, str):
            return float(v) if v else 0.0
        return v

    @field_validator("price", mode="before")
    @classmethod
    def convert_price(cls, v):
        """Convert price to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.stock > 0

    def can_fulfill(self, quantity: int) -> bool:
        """Check if requested quantity can be fulfilled."""
        return self.stock >= quantity

    def reduce_stock(self, quantity: int) -> None:
        """
        Reduce stock by the given quantity.

        Args:
            quantity: Number of items to reduce

        Raises:
            ValueError: If quantity exceeds available stock
        """
        if quantity > self.stock:
            raise ValueError(
                f"Cannot reduce stock by {quantity}. Only {self.stock} available."
            )
        self.stock -= quantity

    def add_stock(self, quantity: int) -> None:
        """Add stock quantity."""
        if quantity < 0:
            raise ValueError("Cannot add negative stock")
        self.stock += quantity

    def add_review(self, review: ProductReview) -> None:
        """
        Add a review and recalculate average rating.

        Args:
            review: New review to add
        """
        self.reviews.append(review)
        self.num_of_reviews = len(self.reviews)
        self._calculate_average_rating()

    def remove_review(self, user_id: str) -> bool:
        """
        Remove a user's review.

        Args:
            user_id: ID of user whose review to remove

        Returns:
            True if review was removed
        """
        initial_count = len(self.reviews)
        self.reviews = [r for r in self.reviews if r.user != user_id]

        if len(self.reviews) < initial_count:
            self.num_of_reviews = len(self.reviews)
            self._calculate_average_rating()
            return True

        return False

    def _calculate_average_rating(self) -> None:
        """Recalculate average rating from all reviews."""
        if not self.reviews:
            self.ratings = 0.0
            return

        total = sum(review.rating for review in self.reviews)
        self.ratings = round(total / len(self.reviews), 1)

    def to_summary_dict(self) -> dict:
        """
        Get product summary for listing views.

        Returns:
            Dict with essential product info
        """
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "ratings": self.ratings,
            "num_of_reviews": self.num_of_reviews,
            "stock": self.stock,
            "category": self.category.value,
            "image": self.images[0].image if self.images else None,
        }
