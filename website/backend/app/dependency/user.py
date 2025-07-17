from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.jwt import verify_access_token
from app.dependency.database import get_db_dep
from app.model.user import User, UserRole

# Base HTTP bearer security scheme
security = HTTPBearer(auto_error=False)

# Role constants using the enum
ROLE_PUBLIC = UserRole.PUBLIC
ROLE_ADMIN = UserRole.ADMIN


async def get_current_user(
    request: Request, db: AsyncSession = get_db_dep
) -> User | None:
    """Get the current authenticated user from the session cookie.

    Returns the user if authenticated, otherwise None.
    """
    # Get access token from cookies
    access_token = request.cookies.get("elanora_session")

    if not access_token:
        return None

    try:
        # Verify and decode the token
        token_data = verify_access_token(access_token)

        # Get the user from the database using correct field names
        result = await db.execute(
            select(User).filter(User.user_id == int(token_data.sub))
        )
        user = result.scalar_one_or_none()

        # Check if user exists and is active (using boolean field)
        if user and user.is_active:
            return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    return None


# Base guard class to eliminate code duplication
class BaseGuard:
    """Base guard class with common authentication logic."""

    async def authenticate_user(self, request: Request, db: AsyncSession) -> User:
        """Authenticate the user and return the User object."""
        user = await get_current_user(request, db)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def check_role(
        self, user: User, required_role: UserRole, min_role: bool = False
    ) -> None:
        """Check if the user has the required role.

        Args:
            user: The user to check
            required_role: The UserRole enum required
            min_role: If True, check if user has minimum role level,
                    otherwise check if user has exact role

        """
        # Define role hierarchy for comparison
        role_hierarchy = {
            UserRole.PUBLIC: 1,
            UserRole.ADMIN: 2,
        }

        user_role_level = role_hierarchy.get(user.role)
        required_role_level = role_hierarchy.get(required_role)

        if user_role_level is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User has invalid role: {user.role}",
            )

        if required_role_level is None:
            raise ValueError(f"Invalid role requirement: {required_role}")

        has_access = (
            (user_role_level >= required_role_level)
            if min_role
            else (user_role_level == required_role_level)
        )

        if not has_access:
            if min_role:
                message = f"Insufficient privileges. Minimum role {required_role.value} required."
            else:
                message = f"Not authorized. Role {required_role.value} required."

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class UserGuard(BaseGuard):
    """Dependency to validate user authentication.

    Returns the current user if authenticated or raises 401 if not.
    """

    async def __call__(self, request: Request, db: AsyncSession = get_db_dep) -> User:
        """Authenticate user for any authenticated user."""
        return await self.authenticate_user(request, db)


class AdminGuard(BaseGuard):
    """Dependency to validate admin user authentication.

    Returns the current user if authenticated and has admin role,
    otherwise raises 403 Forbidden.
    """

    async def __call__(self, request: Request, db: AsyncSession = get_db_dep) -> User:
        """Authenticate user for admin access."""
        user = await self.authenticate_user(request, db)
        self.check_role(user, ROLE_ADMIN)
        return user


class PublicOrAdminGuard(BaseGuard):
    """Dependency that allows both public and admin users (minimum public role)."""

    async def __call__(self, request: Request, db: AsyncSession = get_db_dep) -> User:
        """Authenticate user for public or admin access."""
        user = await self.authenticate_user(request, db)
        self.check_role(user, ROLE_PUBLIC, min_role=True)
        return user


# Utility functions for role checking
def is_admin(user: User) -> bool:
    """Check if user has admin role."""
    return user.role == UserRole.ADMIN


def is_public(user: User) -> bool:
    """Check if user has public role."""
    return user.role == UserRole.PUBLIC


def has_role(user: User, role: UserRole) -> bool:
    """Check if user has specific role."""
    return user.role == role


def has_minimum_role(user: User, minimum_role: UserRole) -> bool:
    """Check if user has at least the minimum role level."""
    role_hierarchy = {
        UserRole.PUBLIC: 1,
        UserRole.ADMIN: 2,
    }

    user_level = role_hierarchy.get(user.role, 0)
    min_level = role_hierarchy.get(minimum_role, 0)

    return user_level >= min_level


# Instantiate the guards for easy reuse
user_guard = UserGuard()
admin_guard = AdminGuard()

# Reusable guard dependency instances
get_user_dep = Depends(user_guard)
get_admin_dep = Depends(admin_guard)
