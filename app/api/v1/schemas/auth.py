"""
Authentication request/response schemas.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """User registration data."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    avatar: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token response."""
    success: bool = True
    token: str
    user: dict


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Password reset request."""
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    def passwords_match(self) -> bool:
        """Check if passwords match."""
        return self.password == self.confirm_password


class ChangePasswordRequest(BaseModel):
    """Change password request (for authenticated users)."""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
