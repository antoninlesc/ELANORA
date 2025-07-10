"""User service layer - Business logic and password management."""

import secrets
from datetime import UTC, datetime
from typing import Any

from core.jwt import create_access_token, create_refresh_token, verify_refresh_token
from crud.user import (
    check_user_exists_by_email,
    check_user_exists_by_username,
    create_user_in_db,
    get_user_by_id,
    get_user_by_username_or_email,
    update_user_password,
    update_user_profile,
)
from fastapi import BackgroundTasks
from model.user import User
from passlib.context import CryptContext
from schema.common.token import TokenData
from schema.requests.user import ProfileUpdateRequest, RegistrationRequest
from sqlalchemy.ext.asyncio import AsyncSession

# Create a passlib context for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service for user-related business logic."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password (str): The plaintext password to be hashed.

        Returns:
            str: The hashed password.

        """
        return str(pwd_context.hash(password))

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a bcrypt hash.

        Args:
            plain_password (str): The plain text password.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if password matches.

        """
        return bool(pwd_context.verify(plain_password, hashed_password))

    @classmethod
    async def authenticate_user(
        cls, db: AsyncSession, login_or_email: str, password: str
    ) -> User | None:
        """Authenticate user with bcrypt password verification.

        Args:
            db (AsyncSession): Database session.
            login_or_email (str): User username or email.
            password (str): Plain text password.

        Returns:
            User | None: User object if authentication successful, None otherwise.

        """
        user = await get_user_by_username_or_email(db, login_or_email)

        if not user:
            return None

        if not user.password:
            return None

        # Verify password using bcrypt
        is_valid = cls.verify_password(password, user.password)

        if is_valid:
            return user

        return None

    @classmethod
    async def login_user(
        cls,
        db: AsyncSession,
        login_or_email: str,
        password: str,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        """Handle user login with business logic.

        Returns:
            Dict with success, message, user, needs_verification, email

        """
        # Authenticate user
        user = await cls.authenticate_user(db, login_or_email, password)

        if not user:
            return {"success": False, "message": "Invalid credentials"}

        # Check if email is verified
        if not user.is_verified_account:
            verification_code = cls._generate_verification_code()
            hashed_code = cls._hash_verification_code(verification_code)

            # Update user's activation code
            user.activation_code = hashed_code
            await db.commit()

            # Add email sending to background tasks
            sks.add_task(
                cls._send_verification_email,
                user.email,
                user.username,
                verification_code,
            )

            return {
                "success": True,
                "message": "Login successful but email verification required",
                "needs_verification": True,
                "email": user.email,
                "code_sent": True,
            }
        user.last_login = datetime.now(UTC)
        await db.commit()

        return {"success": True, "message": "Login successful", "user": user}

    @classmethod
    async def refresh_user_tokens(
        cls, db: AsyncSession, refresh_token: str
    ) -> dict[str, Any]:
        """Handle token refresh with business logic."""
        try:
            # Verify refresh token
            token_data = verify_refresh_token(refresh_token)

            # Get user from database
            user = await get_user_by_id(db, int(token_data.sub))

            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User account is inactive or not found",
                }

            # Create new tokens
            new_token_data = TokenData(sub=str(user.user_id))
            new_access_token = create_access_token(new_token_data)
            new_refresh_token = create_refresh_token(new_token_data)
            csrf_token = secrets.token_hex(16)

            return {
                "success": True,
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "csrf_token": csrf_token,
                "message": "Tokens refreshed successfully",
            }

        except Exception as e:
            return {"success": False, "message": f"Token refresh failed: {e!s}"}

    @classmethod
    async def create_user(
        cls,
        db: AsyncSession,
        registration_data: RegistrationRequest,
    ) -> User:
        """Create a new user with bcrypt password hashing.

        Args:
            db (AsyncSession): Database session.
            registration_data (RegistrationRequest): User registration data.

        Returns:
            User: The created user object.

        Raises:
            ValueError: If user creation validation fails.
            Exception: If database operation fails.

        """
        # Hash the password
        hashed_password = cls.hash_password(registration_data.password)

        # Generate activation code
        activation_code = cls._generate_verification_code()
        hashed_activation_code = cls._hash_verification_code(activation_code)

        # Create user in database
        user = await create_user_in_db(
            db,
            username=registration_data.username,
            hashed_password=hashed_password,
            email=registration_data.email,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            affiliation=registration_data.affiliation,
            department=registration_data.department,
            activation_code=hashed_activation_code,
            phone_number=registration_data.phone_number,
        )

        return user

    @classmethod
    async def update_password(
        cls, db: AsyncSession, user: User, new_password: str
    ) -> bool:
        """Update user's password with bcrypt hashing.

        Args:
            db (AsyncSession): Database session.
            user (User): User object to update.
            new_password (str): New plain text password.

        Returns:
            bool: True if update successful, False otherwise.

        """
        new_password_hash = cls.hash_password(new_password)
        success = await update_user_password(db, user, new_password_hash)

        if success:
            user.updated_at = datetime.now(UTC)
            await db.commit()

        return success

    @classmethod
    async def verify_current_password(cls, user: User, current_password: str) -> bool:
        """Verify user's current password.

        Args:
            user (User): User object.
            current_password (str): Current plain text password.

        Returns:
            bool: True if current password is correct.

        """
        if not user.password:
            return False

        return cls.verify_password(current_password, user.password)

    @classmethod
    async def update_user_profile(
        cls,
        db: AsyncSession,
        user: User,
        profile_data: ProfileUpdateRequest,
    ) -> dict[str, Any]:
        """Update user profile with validation.

        Args:
            db (AsyncSession): Database session.
            user (User): User object to update.
            profile_data (ProfileUpdateRequest): Profile update data.

        Returns:
            Dict[str, Any]: Result with updated fields and success status.

        """
        # Prepare update fields
        update_fields = {}
        updated_field_names = []

        field_mapping = {
            "email": profile_data.email,
            "first_name": profile_data.first_name,
            "last_name": profile_data.last_name,
            "phone_number": profile_data.phone_number,
            "affiliation": profile_data.affiliation,
            "department": profile_data.department,
        }

        for field_name, field_value in field_mapping.items():
            if field_value is not None:
                update_fields[field_name] = field_value
                updated_field_names.append(field_name)

        if not update_fields:
            return {
                "success": False,
                "message": "No fields to update",
                "updated_fields": [],
            }

        update_fields["updated_at"] = datetime.now(UTC)

        # Update in database
        success = await update_user_profile(db, user, **update_fields)

        return {
            "success": success,
            "message": "Profile updated successfully"
            if success
            else "Profile update failed",
            "updated_fields": updated_field_names if success else [],
        }

    @classmethod
    async def check_username_availability(cls, db: AsyncSession, username: str) -> bool:
        """Check if a username is available for registration.

        Args:
            db (AsyncSession): Database session.
            username (str): Username to check.

        Returns:
            bool: True if available, False if taken.

        """
        return not await check_user_exists_by_username(db, username)

    @classmethod
    async def check_email_availability(cls, db: AsyncSession, email: str) -> bool:
        """Check if an email is available for registration.

        Args:
            db (AsyncSession): Database session.
            email (str): Email to check.

        Returns:
            bool: True if available, False if taken.

        """
        return not await check_user_exists_by_email(db, email)

    @classmethod
    async def verify_account(
        cls, db: AsyncSession, email: str, verification_code: str
    ) -> dict[str, Any]:
        """Verify user account with activation code.

        Args:
            db (AsyncSession): Database session.
            email (str): User email.
            verification_code (str): Verification code.

        Returns:
            Dict[str, Any]: Verification result.

        """
        user = await get_user_by_username_or_email(db, email)

        if not user:
            return {"success": False, "message": "User not found"}

        if user.is_verified_account:
            return {"success": False, "message": "Account is already verified"}

        # Verify the activation code
        if not cls.verify_password(verification_code, user.activation_code):
            return {"success": False, "message": "Invalid verification code"}

        # Mark account as verified
        user.is_verified_account = True
        user.updated_at = datetime.now(UTC)
        await db.commit()

        return {"success": True, "message": "Account verified successfully"}

    @classmethod
    async def reset_password(
        cls, db: AsyncSession, email: str, reset_code: str, new_password: str
    ) -> dict[str, Any]:
        """Reset user password with reset code.

        Args:
            db (AsyncSession): Database session.
            email (str): User email.
            reset_code (str): Password reset code.
            new_password (str): New password.

        Returns:
            Dict[str, Any]: Reset result.

        """
        user = await get_user_by_username_or_email(db, email)

        if not user:
            return {"success": False, "message": "User not found"}

        # Verify reset code
        if not cls.verify_password(reset_code, user.activation_code):
            return {"success": False, "message": "Invalid reset code"}

        # Update password
        success = await cls.update_password(db, user, new_password)

        if success:
            # Clear activation code after successful reset
            user.activation_code = ""
            user.updated_at = datetime.now(UTC)
            await db.commit()

            return {"success": True, "message": "Password reset successfully"}

        return {"success": False, "message": "Failed to reset password"}

    @classmethod
    async def get_user_by_email(cls, db: AsyncSession, email: str) -> User | None:
        """Get a user by email address."""
        return await get_user_by_username_or_email(db, email)

    # Private helper methods for business logic
    @staticmethod
    def _generate_verification_code() -> str:
        """Generate a verification code."""
        return secrets.token_hex(8)

    @staticmethod
    def _hash_verification_code(code: str) -> str:
        """Hash verification code."""
        return pwd_context.hash(code)

    @staticmethod
    async def _send_verification_email(
        email: str, username: str, verification_code: str
    ) -> None:
        """Send verification email (background task).

        Args:
            email (str): Recipient email address.
            username (str): Username for personalization.
            verification_code (str): Verification code to include.

        """
        # TODO: Implement email sending logic
        # This would typically use an email service like:
        # - SendGrid
        # - AWS SES
        # - SMTP server
        # - Mailgun

        print(f"Sending verification email to {email} for user {username}")
        print(f"Verification code: {verification_code}")

        # Example implementation structure:
        # await email_service.send_verification_email(
        #     to_email=email,
        #     username=username,
        #     verification_code=verification_code
        # )
        pass

    @staticmethod
    async def _send_password_reset_email(
        email: str, username: str, reset_code: str
    ) -> None:
        """Send password reset email (background task).

        Args:
            email (str): Recipient email address.
            username (str): Username for personalization.
            reset_code (str): Password reset code.

        """
        # TODO: Implement password reset email logic
        print(f"Sending password reset email to {email} for user {username}")
        print(f"Reset code: {reset_code}")
        pass
