from datetime import datetime

from pydantic import EmailStr
from app.schema.common.base import CustomBaseModel


class CityResponse(CustomBaseModel):
    """Response schema for city information."""

    city_id: int
    name: str
    country: str


class AddressResponse(CustomBaseModel):
    """Response schema for address information."""

    address_id: int
    street_number: str | None = None
    street_name: str
    city_id: int
    postal_code: str
    address_line_2: str | None = None
    created_at: datetime
    updated_at: datetime
    city: CityResponse | None = None


class UserResponse(CustomBaseModel):
    """UserResponse schema for user data."""

    user_id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified_account: bool
    created_at: datetime


class UserProfileResponse(CustomBaseModel):
    """Extended user profile response with address."""

    user_id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str | None = None
    affiliation: str
    department: str
    role: str
    is_active: bool
    is_verified_account: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    address: AddressResponse | None = None


class LoginResponse(CustomBaseModel):
    """Response schema for login endpoint."""

    message: str
    user: UserResponse | None = None
    csrf_token: str
    needs_verification: bool = False
    email: str | None = None


class RegistrationResponse(CustomBaseModel):
    """Response schema for successful registration."""

    message: str
    user_id: int
    username: str
    email: EmailStr
    requires_activation: bool = True


class ProfileUpdateResponse(CustomBaseModel):
    """Response schema for profile update."""

    message: str
    updated_fields: list[str]
    address_updated: bool = False


class PasswordUpdateResponse(CustomBaseModel):
    """Response schema for password update."""

    message: str
    updated_at: datetime


class AccountChangeResponse(CustomBaseModel):
    """Response schema for account change request."""

    message: str
    request_id: int
    status: str
    requested_type: int


class ForgotPasswordResponse(CustomBaseModel):
    """Response schema for forgot password request."""

    message: str
    email: EmailStr
    reset_code_sent: bool


class ContactFormResponse(CustomBaseModel):
    """Response schema for contact form submission."""

    message: str
    ticket_id: str | None = None
    submitted_at: str


class ResetPasswordResponse(CustomBaseModel):
    """Response schema for password reset."""

    message: str
    email: str
    reset_successful: bool
