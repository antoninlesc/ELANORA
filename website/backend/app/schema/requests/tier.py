from app.schema.common.base import CustomBaseModel
from typing import Optional


class TierTreeRequest(CustomBaseModel):
    project_name: str


class CreateSectionRequest(CustomBaseModel):
    project_id: int
    name: str


class RenameSectionRequest(CustomBaseModel):
    section_id: int
    new_name: str


class DeleteSectionRequest(CustomBaseModel):
    section_id: int


class MoveTierGroupRequest(CustomBaseModel):
    tier_group_id: int
    section_id: Optional[int]
