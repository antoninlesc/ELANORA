from pydantic import BaseModel, EmailStr, Field


class RegisterWithInvitationRequest(BaseModel):
    invitation_code: str = Field(..., description="Code d'invitation brut")
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    affiliation: str
    department: str
