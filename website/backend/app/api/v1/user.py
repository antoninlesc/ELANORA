from fastapi import APIRouter

from model.user import User
from schema.responses.user import UserResponse
from dependency.user import get_user_dep

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
