from pydantic import BaseModel, EmailStr, Field
from app.schema.requests.user import AddressRequest


class RegisterWithInvitationRequest(BaseModel):
    invitation_code: str = Field(..., description="Code d'invitation brut")
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    phone_number: str | None = None
    affiliation: str
    department: str
    address: AddressRequest | None = None
