import secrets
from typing import Any

from app.core.config import (
    ACCESS_TOKEN_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    CSRF_TOKEN_NAME,
    ENVIRONMENT,
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_PATH,
)
from app.core.jwt import create_access_token, create_refresh_token
from app.core.limiter import limiter
from app.dependency.database import get_db_dep
from app.dependency.user import get_user_dep
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from app.model.user import User
from app.schema.common.token import TokenData
from app.schema.requests.user import (
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schema.requests.register_with_invitation import RegisterWithInvitationRequest
from app.schema.responses.user import LoginResponse, UserResponse
from app.service.user import UserService
from app.service.email_service import EmailService
from app.service.invitation import InvitationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = get_db_dep,
) -> LoginResponse:
    """Handle user login and set JWT tokens as HTTP-only cookies."""
    # Use service layer for authentication
    login_result = await UserService.login_user(
        db=db,
        login_or_email=body.login,
        password=body.password,
        background_tasks=background_tasks,
    )

    if not login_result["success"]:
        raise HTTPException(status_code=400, detail=login_result["message"])

    # Handle email verification case
    if login_result.get("needs_verification"):
        return LoginResponse(
            message=login_result["message"],
            user=None,
            csrf_token="",
            needs_verification=True,
            email=login_result["email"],
        )

    # Get user and create tokens
    user = login_result["user"]
    token_data = TokenData(sub=str(user.user_id))

    # Create tokens
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    csrf_token = secrets.token_hex(16)

    # Set cookies
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=ENVIRONMENT == "prod",
        samesite="lax",
    )

    response.set_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=ENVIRONMENT == "prod",
        samesite="lax",
        path=REFRESH_TOKEN_PATH,
    )

    response.set_cookie(
        CSRF_TOKEN_NAME,
        csrf_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=ENVIRONMENT == "prod",
        samesite="lax",
    )

    user_response = UserResponse(
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

    return LoginResponse(
        message="Login successful, cookies set.",
        user=user_response,
        csrf_token=csrf_token,
    )


@router.post("/refresh")
async def refresh_tokens(
    request: Request, response: Response, db: AsyncSession = get_db_dep
) -> dict[str, Any]:
    """Refresh the access token using the refresh token."""
    # Get refresh token from cookies
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing"
        )

    try:
        # Use service layer for token refresh
        refresh_result = await UserService.refresh_user_tokens(db, refresh_token)

        if not refresh_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=refresh_result["message"],
            )

        # Set new cookies
        response.set_cookie(
            ACCESS_TOKEN_COOKIE_NAME,
            refresh_result["access_token"],
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=ENVIRONMENT == "prod",
            samesite="lax",
        )

        response.set_cookie(
            REFRESH_TOKEN_COOKIE_NAME,
            refresh_result["refresh_token"],
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=ENVIRONMENT == "prod",
            samesite="lax",
            path=REFRESH_TOKEN_PATH,
        )

        response.set_cookie(
            CSRF_TOKEN_NAME,
            refresh_result["csrf_token"],
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=False,
            secure=ENVIRONMENT == "prod",
            samesite="lax",
        )

        return {
            "message": "Tokens refreshed successfully",
            CSRF_TOKEN_NAME: refresh_result["csrf_token"],
        }

    except HTTPException:
        # Clear invalid tokens
        response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
        response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path=REFRESH_TOKEN_PATH)
        raise
    except Exception as e:
        response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
        response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path=REFRESH_TOKEN_PATH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to refresh tokens"
        ) from e


@router.post("/logout")
async def logout(
    response: Response,
    user: User = get_user_dep,
) -> dict[str, Any]:
    """Log out the user by deleting all auth cookies."""
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, path=REFRESH_TOKEN_PATH)
    response.delete_cookie(CSRF_TOKEN_NAME)
    return {"message": "Logged out successfully, cookies cleared."}


@router.get("/check-username/{username}")
async def check_username_availability(
    username: str,
    db: AsyncSession = get_db_dep,
) -> dict[str, Any]:
    """Check if a username is available for registration."""
    try:
        available = await UserService.check_username_availability(db, username)
        return {
            "available": available,
            "message": "Username is available"
            if available
            else "Username is already taken",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking username availability: {e!s}"
        ) from e


@router.get("/check-email/{email}")
async def check_email_availability(
    email: str,
    db: AsyncSession = get_db_dep,
) -> dict[str, Any]:
    """Check if an email is available for registration."""
    try:
        available = await UserService.check_email_availability(db, email)
        return {
            "available": available,
            "message": "Email is available" if available else "Email is already in use",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking email availability: {e!s}"
        ) from e


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = get_db_dep,
) -> dict[str, Any]:
    """Request a password reset via email.

    This endpoint allows a user to request a password reset by providing their email address.
    A verification code will be sent via email if the address exists in the database.

    Args:
        request (Request): The HTTP Request object (required by SlowAPI for rate limiting)
        body (ForgotPasswordRequest): Form data containing email and language
        background_tasks (BackgroundTasks): Background task manager for sending emails
        db (AsyncSession): Database session

    Returns:
        dict[str, Any]: JSON response with a confirmation message

    Raises:
        HTTPException: If an error occurs during request processing

    Note:
        For security reasons, the same response is returned whether the email exists or not
        in the database.

    """
    try:
        # Check if user exists
        user = await UserService.get_user_by_email(db, body.email)

        if user:
            # Generate verification code
            verification_code = UserService._generate_verification_code()
            hashed_code = UserService._hash_verification_code(verification_code)

            # Update user's activation code for password reset
            user.activation_code = hashed_code
            await db.commit()

            # Send password reset email
            email_service = EmailService()
            email_sent = await email_service.send_password_reset_verification_email(
                email=body.email,
                username=user.username,
                code=verification_code,
                language=body.language if hasattr(body, "language") else "en",
            )

            if not email_sent:
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while sending the verification code. Please try again.",
                )

        # Always return the same response for security
        return {
            "message": "If the email address exists in our system, you will receive a password reset code shortly.",
            "success": True,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}",
        ) from e


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: AsyncSession = get_db_dep,
) -> dict[str, Any]:
    """Reset user password with verification code.

    This endpoint allows a user to reset their password using the verification code
    sent via email.

    Args:
        request (Request): The HTTP Request object (required by SlowAPI for rate limiting)
        body (ResetPasswordRequest): Form data containing email, code, and new password
        db (AsyncSession): Database session

    Returns:
        dict[str, Any]: JSON response with success or error message

    Raises:
        HTTPException: If the reset code is invalid or user is not found

    """
    try:
        # Reset password using the service
        result = await UserService.reset_password(
            db=db,
            email=body.email,
            reset_code=body.code,
            new_password=body.new_password,
        )

        if result["success"]:
            return {
                "message": "Password reset successfully. You can now log in with your new password.",
                "success": True,
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while resetting your password: {str(e)}",
        ) from e


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterWithInvitationRequest,
    db: AsyncSession = get_db_dep,
):
    """Register a new user using an invitation code.

    This endpoint allows a user to register using an invitation code.
    It validates the invitation code, creates the user, and marks the invitation as used.
    Args:
        request (RegisterWithInvitationRequest): The request body containing user details and invitation code.
        db (AsyncSession): Database session.

    Returns:
        UserResponse: The registered user details.

    Raises:
        HTTPException: If the invitation code is invalid or expired, or if user creation fails.

    """
    invitation_service = InvitationService()
    user_service = UserService()

    # 1. Validate the invitation code
    invitation_validation = await invitation_service.validate_invitation(
        db, request.invitation_code
    )
    if not invitation_validation.valid or not invitation_validation.invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation invalide ou expirée.",
        )

    invitation_info = invitation_validation.invitation
    # check if the email in the invitation matches the one in the request (if provided)
    if invitation_info.receiver_email and request.email:
        if (
            invitation_info.receiver_email.strip().lower()
            != request.email.strip().lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'email du formulaire ne correspond pas à celui de l'invitation.",
            )

    # 2. Create the user
    is_verified = False
    if (
        invitation_info.receiver_email
        and request.email
        and invitation_info.receiver_email.strip().lower()
        == request.email.strip().lower()
    ):
        is_verified = True

    # Create user using UserService
    user = await user_service.create_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        affiliation=request.affiliation,
        department=request.department,
        is_verified=is_verified,
        phone_number=request.phone_number,
        address_data=request.address,
    )
    # 3. Accept the invitation
    await invitation_service.accept_invitation(
        db, invitation_info.invitation_id, user.user_id
    )
    # 4. Return the user response
    user_response = UserResponse(
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
    return user_response
