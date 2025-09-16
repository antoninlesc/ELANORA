from app.schema.common.base import CustomBaseModel


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
    tier_group_id: int | None
    section_id: int | None
    project_id: int
    tier_id: int
    tier_name: str
