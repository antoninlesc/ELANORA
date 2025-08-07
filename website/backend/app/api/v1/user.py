from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import get_all_active_users
from app.dependency.database import get_db_dep
from app.dependency.user import get_user_dep
from app.model.user import User
from app.schema.responses.user import UserListResponse, UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_data(
    user: User = get_user_dep,
) -> UserResponse:
    """Retrieve the current user object."""
    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
        is_verified_account=user.is_verified_account,
        created_at=user.created_at,
    )


@router.get("/active", response_model=UserListResponse)
async def get_active_users(
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> UserListResponse:
    """Get all active users (for admins or authorized operations)."""
    # This endpoint could be restricted to admins if needed
    users = await get_all_active_users(db)

    return UserListResponse(
        users=[
            UserResponse(
                user_id=u.user_id,
                username=u.username,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role.value,
                is_active=u.is_active,
                is_verified_account=u.is_verified_account,
                created_at=u.created_at,
            )
            for u in users
        ]
    )
