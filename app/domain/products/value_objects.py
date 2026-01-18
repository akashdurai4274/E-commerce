"""
Product domain value objects.
Immutable objects that represent product-related concepts.
"""
from enum import Enum


class ProductCategory(str, Enum):
    """
    Enumeration of valid product categories.

    Using str, Enum allows direct string serialization in Pydantic models
    while maintaining type safety and validation.
    """
    ELECTRONICS = "Electronics"
    MOBILE_PHONES = "Mobile Phones"
    LAPTOPS = "Laptops"
    ACCESSORIES = "Accessories"
    HEADPHONES = "Headphones"
    FOOD = "Food"
    BOOKS = "Books"
    CLOTHES_SHOES = "Clothes/Shoes"
    BEAUTY_HEALTH = "Beauty/Health"
    SPORTS = "Sports"
    OUTDOOR = "Outdoor"
    HOME = "Home"

    @classmethod
    def values(cls) -> list[str]:
        """Return all category values as strings."""
        return [category.value for category in cls]
