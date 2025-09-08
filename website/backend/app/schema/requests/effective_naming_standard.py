from pydantic import BaseModel


class AssignEffectiveNamingStandardRequest(BaseModel):
    naming_standard_id: int
