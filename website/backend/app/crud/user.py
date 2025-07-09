"""User CRUD operations - Pure database access layer."""

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from model.user import User, UserRole

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
    username: str,
    hashed_password: str,
    email: str,
    first_name: str,
    last_name: str,
    affiliation: str,
    department: str,
    activation_code: str,
    address_id: int | None = None,
    **additional_fields,
) -> User:
    """Create a new user in the database.

    Args:
        db (AsyncSession): Database session.
        username (str): User username.
        hashed_password (str): Already hashed password.
        email (str): User email.
        first_name (str): User's first name.
        last_name (str): User's last name.
        affiliation (str): User's affiliation.
        department (str): User's department.
        activation_code (str): Activation code.
        address_id (int | None): Optional address ID.
        **additional_fields: Additional user fields.

    Returns:
        User: The created user object.

    Raises:
        Exception: If user creation fails.
    """
    user = User(
        username=username,
        password=hashed_password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        affiliation=affiliation,
        department=department,
        activation_code=activation_code,
        address_id=address_id,
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
    query = select(User.email).where(User.role == ROLE_ADMIN, User.is_active == True)
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
