"""
Product service.
Handles product management and queries.
"""
from typing import Optional, List, Tuple
from decimal import Decimal

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.domain.products.entities import Product, ProductImage, ProductReview
from app.domain.products.value_objects import ProductCategory
from app.infrastructure.repositories.product_repository import MongoProductRepository

logger = get_logger(__name__)


class ProductService:
    """
    Product management service.

    Handles:
    - Product CRUD operations
    - Product search and filtering
    - Review management
    - Stock management
    """

    def __init__(self, product_repository: MongoProductRepository):
        """Initialize product service."""
        self._product_repo = product_repository

    async def get_product(self, product_id: str) -> Product:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product entity

        Raises:
            NotFoundError: If product not found
        """
        product = await self._product_repo.get_by_id(product_id)

        if not product:
            raise NotFoundError("Product not found")

        return product

    async def get_products(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Get products with filtering and pagination.

        Args:
            keyword: Search keyword
            category: Category filter
            min_price: Minimum price
            max_price: Maximum price
            min_rating: Minimum rating
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (products, total count)
        """
        skip = (page - 1) * limit

        products, total = await self._product_repo.filter_products(
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            skip=skip,
            limit=limit
        )

        return products, total

    async def create_product(
        self,
        name: str,
        price: int,
        description: str,
        category: ProductCategory,
        seller: str,
        stock: int,
        images: List[dict],
        user_id: str
    ) -> Product:
        """
        Create a new product.

        Args:
            name: Product name
            price: Product price
            description: Product description
            category: Product category
            seller: Seller name
            stock: Initial stock
            images: List of image dicts
            user_id: ID of user creating product

        Returns:
            Created product
        """
        product_images = [
            ProductImage(image=img.get("image", img))
            for img in images
        ]

        product = Product(
            name=name,
            price=price,
            description=description,
            category=category,
            seller=seller,
            stock=stock,
            images=product_images,
            user=user_id
        )

        created_product = await self._product_repo.create(product)

        logger.info(
            "Product created",
            product_id=created_product.id,
            name=name
        )

        return created_product

    async def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        price: Optional[int] = None,
        description: Optional[str] = None,
        category: Optional[ProductCategory] = None,
        seller: Optional[str] = None,
        stock: Optional[int] = None,
        images: Optional[List[dict]] = None
    ) -> Product:
        """
        Update product.

        Args:
            product_id: Product ID
            name: New name
            price: New price
            description: New description
            category: New category
            seller: New seller
            stock: New stock
            images: New images

        Returns:
            Updated product
        """
        product = await self.get_product(product_id)

        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        if description is not None:
            product.description = description
        if category is not None:
            product.category = category
        if seller is not None:
            product.seller = seller
        if stock is not None:
            product.stock = stock
        if images is not None:
            product.images = [
                ProductImage(image=img.get("image", img))
                for img in images
            ]

        updated_product = await self._product_repo.update(product)

        logger.info("Product updated", product_id=product_id)

        return updated_product

    async def delete_product(self, product_id: str) -> bool:
        """
        Delete product.

        Args:
            product_id: Product ID

        Returns:
            True if deleted
        """
        # Verify exists
        await self.get_product(product_id)

        success = await self._product_repo.delete(product_id)

        if success:
            logger.info("Product deleted", product_id=product_id)

        return success

    async def add_review(
        self,
        product_id: str,
        user_id: str,
        rating: float,
        comment: str
    ) -> Product:
        """
        Add or update product review.

        Args:
            product_id: Product ID
            user_id: User ID
            rating: Rating value
            comment: Review comment

        Returns:
            Updated product
        """
        # Verify product exists
        await self.get_product(product_id)

        await self._product_repo.add_review(
            product_id=product_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )

        logger.info(
            "Review added",
            product_id=product_id,
            user_id=user_id
        )

        return await self.get_product(product_id)

    async def delete_review(
        self,
        product_id: str,
        user_id: str
    ) -> bool:
        """
        Delete user's review.

        Args:
            product_id: Product ID
            user_id: User ID

        Returns:
            True if deleted
        """
        success = await self._product_repo.remove_review(product_id, user_id)

        if success:
            logger.info(
                "Review deleted",
                product_id=product_id,
                user_id=user_id
            )

        return success

    async def update_stock(
        self,
        product_id: str,
        quantity_change: int
    ) -> bool:
        """
        Update product stock.

        Args:
            product_id: Product ID
            quantity_change: Amount to add/subtract

        Returns:
            True if updated
        """
        success = await self._product_repo.update_stock(
            product_id,
            quantity_change
        )

        if success:
            logger.info(
                "Stock updated",
                product_id=product_id,
                change=quantity_change
            )

        return success

    async def get_admin_products(
        self,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Get all products for admin.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Tuple of (products, total)
        """
        skip = (page - 1) * limit
        return await self._product_repo.get_admin_products(skip, limit)

    async def get_top_rated(self, limit: int = 10) -> List[Product]:
        """Get top rated products."""
        return await self._product_repo.get_top_rated(limit)
