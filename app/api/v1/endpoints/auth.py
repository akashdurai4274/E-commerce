"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status

from app.api.v1.dependencies import AuthServiceDep, CurrentUser
from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.api.v1.schemas.common import MessageResponse
from app.api.v1.schemas.users import UserResponse
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError,
    NotFoundError,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthServiceDep
):
    """
    Register a new user account.

    Returns JWT token and user data on successful registration.
    """
    try:
        user, token = await auth_service.register(
            name=request.name,
            email=request.email,
            password=request.password,
            avatar=request.avatar
        )

        return TokenResponse(
            token=token,
            user=user.to_public_dict()
        )

    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthServiceDep
):
    """
    Authenticate user and return JWT token.
    """
    try:
        user, token = await auth_service.login(
            email=request.email,
            password=request.password
        )

        return TokenResponse(
            token=token,
            user=user.to_public_dict()
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser
):
    """
    Get current authenticated user's profile.
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        avatar=current_user.avatar,
        role=current_user.role.value,
        created_at=current_user.created_at
    )


@router.post("/password/forgot", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthServiceDep
):
    """
    Request password reset email.

    In production, this would send an email with reset link.
    For development, returns success message.
    """
    try:
        reset_token = await auth_service.forgot_password(request.email)

        # In production, send email here
        # For now, just return success
        return MessageResponse(
            message="If this email exists, a password reset link has been sent"
        )

    except NotFoundError:
        # Don't reveal if email exists
        return MessageResponse(
            message="If this email exists, a password reset link has been sent"
        )


@router.put("/password/reset/{token}", response_model=MessageResponse)
async def reset_password(
    token: str,
    request: ResetPasswordRequest,
    auth_service: AuthServiceDep
):
    """
    Reset password using token from email.
    """
    if not request.passwords_match():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    try:
        await auth_service.reset_password(token, request.password)

        return MessageResponse(
            message="Password reset successful"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/password/update", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep
):
    """
    Change password for authenticated user.
    """
    try:
        await auth_service.change_password(
            user_id=current_user.id,
            old_password=request.old_password,
            new_password=request.new_password
        )

        return MessageResponse(
            message="Password updated successfully"
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: CurrentUser):
    """
    Logout user.

    With JWT, logout is handled client-side by removing the token.
    This endpoint is for API consistency.
    """
    return MessageResponse(
        message="Logged out successfully"
    )
