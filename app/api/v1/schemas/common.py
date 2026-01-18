"""
Common schema types used across the API.
"""
from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Simple message response."""
    success: bool = True
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Provides consistent pagination structure across all list endpoints.
    """
    success: bool = True
    count: int = Field(..., description="Number of items in current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    results_per_page: int = Field(..., description="Items per page")
    data: List[Any] = Field(..., description="List of items")


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    errors: Optional[List[dict]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    app: str
    version: str
    environment: str
