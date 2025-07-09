import secrets
from typing import Any

from core.config import (
    ACCESS_TOKEN_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    CSRF_TOKEN_NAME,
    ENVIRONMENT,
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_PATH,
)
from core.jwt import create_access_token, create_refresh_token
from core.limiter import limiter
from dependency.database import get_db_dep
from dependency.user import get_user_dep
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from model.user import User
from schema.common.token import TokenData
from schema.requests.user import LoginRequest
from schema.responses.user import LoginResponse, UserResponse
from service.user import UserService
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
