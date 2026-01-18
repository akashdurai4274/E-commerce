"""
Custom exception classes for the application.
Provides consistent error handling across all domains.
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Base application exception.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "success": False,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# ===================
# Authentication Errors
# ===================

class AuthenticationError(AppException):
    """Base class for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid authentication token"):
        super().__init__(message)


class InvalidResetTokenError(AppException):
    """Raised when password reset token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired reset token"):
        super().__init__(message, status_code=400)


# ===================
# Authorization Errors
# ===================

class AuthorizationError(AppException):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class InsufficientRoleError(AuthorizationError):
    """Raised when user's role is insufficient."""

    def __init__(self, required_role: str):
        super().__init__(
            f"This action requires {required_role} role"
        )
        self.details = {"required_role": required_role}


# ===================
# Resource Errors
# ===================

class NotFoundError(AppException):
    """Base class for resource not found errors."""

    def __init__(self, message: str = "Resource not found", identifier: Any = None):
        details = {}
        if identifier:
            details["identifier"] = str(identifier)
        super().__init__(
            message=message,
            status_code=404,
            details=details
        )


class ConflictError(AppException):
    """Raised when there is a conflict with existing resource."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class ForbiddenError(AppException):
    """Raised when access to resource is forbidden."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status_code=403)


class PaymentError(AppException):
    """Raised when payment processing fails."""

    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message, status_code=400)


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""

    def __init__(self, identifier: Any = None):
        super().__init__("User not found", identifier)


class ProductNotFoundError(NotFoundError):
    """Raised when a product is not found."""

    def __init__(self, identifier: Any = None):
        super().__init__("Product not found", identifier)


class OrderNotFoundError(NotFoundError):
    """Raised when an order is not found."""

    def __init__(self, identifier: Any = None):
        super().__init__("Order not found", identifier)


class ReviewNotFoundError(NotFoundError):
    """Raised when a review is not found."""

    def __init__(self, identifier: Any = None):
        super().__init__("Review not found", identifier)


# ===================
# Validation Errors
# ===================

class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class DuplicateError(AppException):
    """Raised when trying to create a duplicate resource."""

    def __init__(self, field: str, value: Any):
        super().__init__(
            message=f"Duplicate {field}: {value}",
            status_code=409,
            details={"field": field, "value": str(value)}
        )


class UserAlreadyExistsError(DuplicateError):
    """Raised when trying to register with an existing email."""

    def __init__(self, email: str):
        super().__init__("email", email)


# ===================
# Business Logic Errors
# ===================

class BusinessRuleError(AppException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class InsufficientStockError(BusinessRuleError):
    """Raised when product stock is insufficient for an order."""

    def __init__(
        self,
        product_id: str,
        product_name: str,
        requested: int,
        available: int
    ):
        super().__init__(
            message=f"Insufficient stock for {product_name}. "
                    f"Requested: {requested}, Available: {available}",
            details={
                "product_id": product_id,
                "product_name": product_name,
                "requested": requested,
                "available": available
            }
        )


class OrderAlreadyDeliveredError(BusinessRuleError):
    """Raised when trying to modify a delivered order."""

    def __init__(self, order_id: str):
        super().__init__(
            f"Order {order_id} has already been delivered",
            details={"order_id": order_id}
        )


class PaymentRequiredError(BusinessRuleError):
    """Raised when payment is required but not completed."""

    def __init__(self, order_id: str):
        super().__init__(
            f"Payment required for order {order_id}",
            details={"order_id": order_id}
        )


class ReviewAlreadyExistsError(BusinessRuleError):
    """Raised when user has already reviewed a product."""

    def __init__(self, product_id: str, user_id: str):
        super().__init__(
            "You have already reviewed this product",
            details={"product_id": product_id, "user_id": user_id}
        )


# ===================
# External Service Errors
# ===================

class ExternalServiceError(AppException):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=502,
            error_code=f"{service}Error",
            details=details or {}
        )


class PaymentGatewayError(ExternalServiceError):
    """Raised when payment gateway (Stripe) fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("PaymentGateway", message, details)


class EmailServiceError(ExternalServiceError):
    """Raised when email service fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("EmailService", message, details)


class OAuthProviderError(ExternalServiceError):
    """Raised when OAuth provider call fails."""

    def __init__(
        self,
        provider: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(f"OAuth.{provider}", message, details)


# ===================
# File Handling Errors
# ===================

class FileUploadError(AppException):
    """Raised when file upload fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class FileTooLargeError(FileUploadError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, max_size: int, actual_size: int):
        super().__init__(
            f"File size exceeds maximum allowed size of {max_size / 1024 / 1024:.1f}MB",
            details={
                "max_size_bytes": max_size,
                "actual_size_bytes": actual_size
            }
        )


class InvalidFileTypeError(FileUploadError):
    """Raised when uploaded file type is not allowed."""

    def __init__(self, file_type: str, allowed_types: list[str]):
        super().__init__(
            f"File type '{file_type}' is not allowed",
            details={
                "file_type": file_type,
                "allowed_types": allowed_types
            }
        )


# ===================
# Kafka/Event Errors
# ===================

class EventPublishError(AppException):
    """Raised when event publishing fails."""

    def __init__(self, topic: str, message: str):
        super().__init__(
            message=f"Failed to publish event to {topic}: {message}",
            status_code=500,
            details={"topic": topic}
        )


class EventConsumerError(AppException):
    """Raised when event consumption fails."""

    def __init__(self, topic: str, message: str):
        super().__init__(
            message=f"Failed to consume event from {topic}: {message}",
            status_code=500,
            details={"topic": topic}
        )
