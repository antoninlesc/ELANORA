from pydantic import BaseModel


class InstanceResponse(BaseModel):
    instance_name: str
    contact_email: str
    max_file_size_mb: float
    max_users: int
