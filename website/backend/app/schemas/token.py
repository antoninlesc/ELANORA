from pydantic import EmailStr

from .base import CustomBaseModel

class TokenData(CustomBaseModel):
    """TokenData schema for user authentication.

    Attributes:
        sub (str): The subject identifier for the user (user ID).

    """

    sub: str