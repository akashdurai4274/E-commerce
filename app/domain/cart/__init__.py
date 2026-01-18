"""
Cart domain module.
Cart is managed client-side but we provide schemas for validation.
"""
from app.domain.cart.entities import CartItem, Cart

__all__ = ["CartItem", "Cart"]
