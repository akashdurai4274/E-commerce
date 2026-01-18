"""
Product repository interface.
Defines the contract for product data access operations.
"""
from abc import abstractmethod
from typing import Optional, List, Tuple

from app.domain.shared.repository import BaseRepository
from app.domain.products.entities import Product
from app.domain.products.value_objects import ProductCategory


class ProductRepository(BaseRepository[Product]):
    """
    Product repository interface.

    Extends base repository with product-specific operations.
    """

    @abstractmethod
    async def search(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Search products by keyword in name and description.

        Args:
            keyword: Search keyword
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (products, total count)
        """
        pass

    @abstractmethod
    async def get_by_category(
        self,
        category: ProductCategory,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Get products by category.

        Args:
            category: Product category
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (products, total count)
        """
        pass

    @abstractmethod
    async def get_by_seller(
        self,
        seller: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Get products by seller.

        Args:
            seller: Seller name
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (products, total count)
        """
        pass

    @abstractmethod
    async def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Get products within a price range.

        Args:
            min_price: Minimum price
            max_price: Maximum price
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (products, total count)
        """
        pass

    @abstractmethod
    async def get_top_rated(
        self,
        limit: int = 10
    ) -> List[Product]:
        """
        Get top-rated products.

        Args:
            limit: Maximum to return

        Returns:
            List of top-rated products
        """
        pass

    @abstractmethod
    async def update_stock(
        self,
        product_id: str,
        quantity_change: int
    ) -> bool:
        """
        Update product stock.

        Args:
            product_id: Product ID
            quantity_change: Amount to add (positive) or subtract (negative)

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def add_review(
        self,
        product_id: str,
        user_id: str,
        rating: float,
        comment: str
    ) -> bool:
        """
        Add or update a review for a product.

        Args:
            product_id: Product ID
            user_id: User ID
            rating: Rating value
            comment: Review comment

        Returns:
            True if review was added/updated
        """
        pass

    @abstractmethod
    async def remove_review(
        self,
        product_id: str,
        user_id: str
    ) -> bool:
        """
        Remove a user's review from a product.

        Args:
            product_id: Product ID
            user_id: User ID

        Returns:
            True if review was removed
        """
        pass

    @abstractmethod
    async def get_admin_products(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Get all products for admin panel.

        Args:
            skip: Number to skip
            limit: Maximum to return

        Returns:
            Tuple of (products, total count)
        """
        pass
