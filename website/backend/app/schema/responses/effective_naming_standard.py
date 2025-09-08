from pydantic import BaseModel


class EffectiveNamingStandardOut(BaseModel):
    id: int
    project_id: int
    project_file_type_id: int
    naming_standard_id: int


class EffectiveNamingStandardResponse(BaseModel):
    success: bool
    effective_standard: EffectiveNamingStandardOut


class UnassignEffectiveNamingStandardResponse(BaseModel):
    success: bool


class GetEffectiveStandardsResponse(BaseModel):
    effective_standards: list[EffectiveNamingStandardOut]
