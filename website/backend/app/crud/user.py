"""User CRUD operations - Pure database access layer."""

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.user import User, UserRole
from app.schema.common.user import UserCreateData
from app.utils.database import DatabaseUtils

ROLE_ADMIN = UserRole.ADMIN


async def get_user_by_id(
    db: AsyncSession, user_id: int, load_relationships: bool = False
) -> User | None:
    """Retrieve a user by their ID with optional relationship loading."""
    options = None
    if load_relationships:
        options = [
            selectinload(User.address),
            selectinload(User.notification_preference),
        ]
    return await DatabaseUtils.get_by_id(db, User, "user_id", user_id, options=options)


async def get_user_by_username_or_email(
    db: AsyncSession, login_or_email: str
) -> User | None:
    """Retrieve a user by their username or email using efficient OR condition."""
    conditions = [or_(User.username == login_or_email, User.email == login_or_email)]
    return await DatabaseUtils.get_one_or_none(db, User, conditions=conditions)


async def create_user_in_db(
    db: AsyncSession,
    user_data: UserCreateData,
    **additional_fields,
) -> User:
    """Create a new user in the database."""
    user = User(
        username=user_data.username,
        hashed_password=user_data.hashed_password,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        affiliation=user_data.affiliation,
        department=user_data.department,
        activation_code=user_data.activation_code,
        address_id=user_data.address_id,
        is_verified_account=user_data.is_verified_account,
        role=UserRole.PUBLIC,
        is_active=True,
        **additional_fields,
    )
    # Use DatabaseUtils for create and commit
    return await DatabaseUtils.create(db, user)


async def update_user_password(
    db: AsyncSession, user_id: int, new_password_hash: str
) -> int:
    """Update user's password hash in database. Returns number of updated rows."""
    filters = {"user_id": user_id}
    update_fields = {"hashed_password": new_password_hash}
    return await DatabaseUtils.update_by_filter(db, User, filters, update_fields)


async def update_user_profile(db: AsyncSession, user_id: int, **update_fields) -> int:
    """Update user profile fields in database. Returns number of updated rows."""
    filters = {"user_id": user_id}
    return await DatabaseUtils.update_by_filter(db, User, filters, update_fields)


async def validate_user_exists_and_active(db: AsyncSession, user_id: int) -> bool:
    """Validate that a user exists and has an active account."""
    filters = {"user_id": user_id, "is_active": True}
    user = await DatabaseUtils.get_one_or_none(db, User, filters=filters)
    return user is not None


async def get_admin_emails(db: AsyncSession) -> list[str]:
    """Get email addresses of all site administrators."""
    filters = {"role": ROLE_ADMIN, "is_active": True}
    admins = await DatabaseUtils.get_by_filter(db, User, filters)
    admin_emails = [admin.email for admin in admins if admin.email]
    return admin_emails or ["admin@example.com"]


async def check_user_exists_by_username(db: AsyncSession, username: str) -> bool:
    """Check if a user with the given username exists."""
    return await DatabaseUtils.exists(db, User, "username", username)


async def check_user_exists_by_email(db: AsyncSession, email: str) -> bool:
    """Check if a user with the given email exists."""
    return await DatabaseUtils.exists(db, User, "email", email)


async def get_all_active_users(
    db: AsyncSession, limit: int | None = None, offset: int | None = None
) -> list[User]:
    """Get all active users with optional pagination."""
    filters = {"is_active": True}
    order_by = [User.username]
    return await DatabaseUtils.get_by_filter(
        db, User, filters, order_by=order_by, limit=limit, offset=offset
    )


async def get_users_by_role(
    db: AsyncSession, role: UserRole, active_only: bool = True
) -> list[User]:
    """Get users by their role."""
    conditions = [User.role == role]
    if active_only:
        conditions.append(User.is_active.is_(True))
    order_by = [User.username]
    return await DatabaseUtils.get_by_conditions(
        db, User, conditions=conditions, order_by=order_by
    )
