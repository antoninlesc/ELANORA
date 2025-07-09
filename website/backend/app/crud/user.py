"""User CRUD operations - Pure database access layer."""

from model.user import User, UserRole
from schema.common.user import UserCreateData
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

ROLE_ADMIN = UserRole.ADMIN


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Retrieve a user by their ID with relationships pre-loaded.

    Args:
        db (AsyncSession): The database session to use for the query.
        user_id (int): The ID of the user to retrieve.

    Returns:
        User or None: The user object if found, otherwise None.

    """
    result = await db.execute(
        select(User).options(selectinload(User.address)).filter(User.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_username_or_email(
    db: AsyncSession, login_or_email: str
) -> User | None:
    """Retrieve a user by their username or email.

    Args:
        db (AsyncSession): The database session to use for the query.
        login_or_email (str): The username or email to search for.

    Returns:
        User: The user object if found, otherwise None.

    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.address))
        .filter(
            or_(
                User.username == login_or_email,
                User.email == login_or_email,
            )
        )
    )
    user = result.scalars().first()
    return user


async def create_user_in_db(
    db: AsyncSession,
    user_data: UserCreateData,
    **additional_fields,
) -> User:
    """Create a new user in the database.

    Args:
        db (AsyncSession): Database session.
        user_data (UserCreateData): User creation data.
        **additional_fields: Additional user fields.

    Returns:
        User: The created user object.

    Raises:
        Exception: If user creation fails.

    """
    user = User(
        username=user_data.username,
        password=user_data.hashed_password,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        affiliation=user_data.affiliation,
        department=user_data.department,
        activation_code=user_data.activation_code,
        address_id=user_data.address_id,
        is_verified_account=False,
        role=UserRole.PUBLIC,
        is_active=True,
        **additional_fields,
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise


async def update_user_password(
    db: AsyncSession, user: User, new_password_hash: str
) -> bool:
    """Update user's password hash in database.

    Args:
        db (AsyncSession): Database session.
        user (User): User object to update.
        new_password_hash (str): New hashed password.

    Returns:
        bool: True if update successful, False otherwise.

    """
    try:
        user.password = new_password_hash
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False


async def update_user_profile(db: AsyncSession, user: User, **update_fields) -> bool:
    """Update user profile fields in database.

    Args:
        db (AsyncSession): Database session.
        user (User): User object to update.
        **update_fields: Fields to update.

    Returns:
        bool: True if update successful, False otherwise.

    """
    try:
        for field, value in update_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False


async def validate_user_exists_and_active(db: AsyncSession, user_id: int) -> bool:
    """Validate that a user exists and has an active account.

    Args:
        db (AsyncSession): The database session to use for the query.
        user_id (int): The ID of the user to validate.

    Returns:
        bool: True if the user exists and is active, False otherwise.

    """
    result = await db.execute(select(User.is_active).filter(User.user_id == user_id))
    is_active = result.scalar_one_or_none()
    return bool(is_active)  # Already boolean


async def get_admin_emails(db: AsyncSession) -> list[str]:
    """Get email addresses of all site administrators.

    Args:
        db: Database session

    Returns:
        list[str]: A list of administrator email addresses.

    """
    query = select(User.email).where(User.role == ROLE_ADMIN, User.is_active)
    result = await db.execute(query)
    admin_emails = result.scalars().all()

    if not admin_emails:
        return ["admin@example.com"]

    return list(admin_emails)


async def check_user_exists_by_username(db: AsyncSession, username: str) -> bool:
    """Check if a user with the given username exists.

    Args:
        db (AsyncSession): Database session.
        username (str): Username to check.

    Returns:
        bool: True if user exists, False otherwise.

    """
    result = await db.execute(select(User.user_id).filter(User.username == username))
    return result.scalar_one_or_none() is not None


async def check_user_exists_by_email(db: AsyncSession, email: str) -> bool:
    """Check if a user with the given email exists.

    Args:
        db (AsyncSession): Database session.
        email (str): Email to check.

    Returns:
        bool: True if user exists, False otherwise.

    """
    result = await db.execute(select(User.user_id).filter(User.email == email))
    return result.scalar_one_or_none() is not None
