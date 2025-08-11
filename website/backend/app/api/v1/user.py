from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.user import get_all_active_users
from app.dependency.database import get_db_dep
from app.dependency.user import get_user_dep
from app.model.user import User
from app.model.address import Address
from app.model.city import City
from app.schema.responses.user import (
    AddressResponse,
    UserListResponse,
    UserProfileResponse,
    UserResponse,
    CityResponse,
)
from app.utils.database import DatabaseUtils

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


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_current_user_profile(
    user: User = get_user_dep,
    db: AsyncSession = get_db_dep,
) -> UserProfileResponse:
    """Retrieve the current user's complete profile including address."""
    # Fetch user with address, city, and country relationships preloaded
    user_with_address = await DatabaseUtils.get_by_id(
        db,
        User,
        "user_id",
        user.user_id,
        options=[
            selectinload(User.address)
            .selectinload(Address.city)
            .selectinload(City.country)
        ]
    )

    address_data = None
    if user_with_address and user_with_address.address:
        city_obj = user_with_address.address.city
        city_response = None
        if city_obj:
            city_response = CityResponse(
                city_id=city_obj.city_id,
                name=city_obj.city_name,
                country=city_obj.country.country_name if city_obj.country else None,
            )
        address_data = AddressResponse(
            address_id=user_with_address.address.address_id,
            street_number=user_with_address.address.street_number,
            street_name=user_with_address.address.street_name,
            city_id=user_with_address.address.city_id,
            postal_code=user_with_address.address.postal_code,
            address_line_2=user_with_address.address.address_line_2,
            created_at=user_with_address.address.created_at,
            updated_at=user_with_address.address.updated_at,
            city=city_response,
        )

    # Use current user data or fetched user data
    target_user = user_with_address or user

    return UserProfileResponse(
        user_id=target_user.user_id,
        username=target_user.username,
        email=target_user.email,
        first_name=target_user.first_name,
        last_name=target_user.last_name,
        phone_number=target_user.phone_number,
        affiliation=target_user.affiliation,
        department=target_user.department,
        role=target_user.role.value,
        is_active=target_user.is_active,
        is_verified_account=target_user.is_verified_account,
        created_at=target_user.created_at,
        updated_at=target_user.updated_at,
        last_login=target_user.last_login,
        address=address_data,
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
