"""
User management endpoints.
"""
from math import ceil

from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File

from app.api.v1.dependencies import UserServiceDep, CurrentUser, CurrentAdmin
from app.api.v1.schemas.users import (
    UserResponse,
    UserUpdateRequest,
    AdminUserUpdateRequest,
)
from app.api.v1.schemas.common import MessageResponse
from app.core.exceptions import NotFoundError, ConflictError

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: CurrentUser,
    user_service: UserServiceDep
):
    """
    Get current user's profile.
    """
    profile = await user_service.get_user_profile(current_user.id)

    return UserResponse(
        id=profile["id"],
        name=profile["name"],
        email=profile["email"],
        avatar=profile.get("avatar"),
        role=profile["role"],
        created_at=profile.get("created_at")
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: UserUpdateRequest,
    current_user: CurrentUser,
    user_service: UserServiceDep
):
    """
    Update current user's profile.
    """
    try:
        updated_user = await user_service.update_profile(
            user_id=current_user.id,
            name=request.name,
            email=request.email,
            avatar=request.avatar
        )

        return UserResponse(
            id=updated_user.id,
            name=updated_user.name,
            email=updated_user.email,
            avatar=updated_user.avatar,
            role=updated_user.role.value,
            created_at=updated_user.created_at
        )

    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/avatar", response_model=MessageResponse)
async def update_avatar(
    avatar: str,
    current_user: CurrentUser,
    user_service: UserServiceDep
):
    """
    Update user's avatar URL.
    """
    await user_service.update_avatar(current_user.id, avatar)

    return MessageResponse(message="Avatar updated successfully")


# Admin endpoints

@router.get("/admin/users")
async def get_all_users(
    current_admin: CurrentAdmin,
    user_service: UserServiceDep,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get all users (admin only).
    """
    users, total = await user_service.get_all_users(
        skip=(page - 1) * limit,
        limit=limit
    )

    return {
        "success": True,
        "count": len(users),
        "total": total,
        "page": page,
        "pages": ceil(total / limit) if total > 0 else 1,
        "users": [
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                avatar=user.avatar,
                role=user.role.value,
                created_at=user.created_at
            )
            for user in users
        ]
    }


@router.get("/admin/user/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_admin: CurrentAdmin,
    user_service: UserServiceDep
):
    """
    Get user by ID (admin only).
    """
    try:
        user = await user_service.get_user_by_id(user_id)

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar=user.avatar,
            role=user.role.value,
            created_at=user.created_at
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/admin/user/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: str,
    request: AdminUserUpdateRequest,
    current_admin: CurrentAdmin,
    user_service: UserServiceDep
):
    """
    Update user by ID (admin only).
    """
    try:
        updated_user = await user_service.admin_update_user(
            user_id=user_id,
            name=request.name,
            email=request.email,
            role=request.role
        )

        return UserResponse(
            id=updated_user.id,
            name=updated_user.name,
            email=updated_user.email,
            avatar=updated_user.avatar,
            role=updated_user.role.value,
            created_at=updated_user.created_at
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/admin/user/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_admin: CurrentAdmin,
    user_service: UserServiceDep
):
    """
    Delete user by ID (admin only).
    """
    try:
        await user_service.delete_user(user_id)

        return MessageResponse(message="User deleted successfully")

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
