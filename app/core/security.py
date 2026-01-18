"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and OAuth.
"""
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically user_id and role)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload or None if invalid

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_password_reset_token() -> tuple[str, str]:
    """
    Generate a password reset token.

    Returns:
        Tuple of (raw_token, hashed_token)
        - raw_token: Send to user via email
        - hashed_token: Store in database
    """
    raw_token = secrets.token_hex(32)
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, hashed_token


def verify_password_reset_token(raw_token: str, stored_hash: str) -> bool:
    """
    Verify a password reset token.

    Args:
        raw_token: Token received from user
        stored_hash: Hashed token stored in database

    Returns:
        True if token is valid, False otherwise
    """
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return secrets.compare_digest(token_hash, stored_hash)


def generate_oauth_state() -> str:
    """
    Generate a secure random state for OAuth flows.

    Returns:
        Random state string for CSRF protection
    """
    return secrets.token_urlsafe(32)


class TokenPayload:
    """Represents decoded JWT token payload."""

    def __init__(
        self,
        sub: str,
        role: str = "user",
        exp: Optional[datetime] = None,
        token_type: str = "access"
    ):
        self.sub = sub  # User ID
        self.role = role
        self.exp = exp
        self.token_type = token_type

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from decoded JWT dict."""
        return cls(
            sub=data.get("sub", ""),
            role=data.get("role", "user"),
            exp=data.get("exp"),
            token_type=data.get("type", "access")
        )
