from dataclasses import dataclass


@dataclass
class UserCreateData:
    """Data class for user creation parameters."""

    username: str
    hashed_password: str
    email: str
    first_name: str
    last_name: str
    affiliation: str
    department: str
    activation_code: str
    address_id: int | None = None
