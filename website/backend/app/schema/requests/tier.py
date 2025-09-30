from app.schema.common.base import CustomBaseModel


class TierTreeRequest(CustomBaseModel):
    project_name: str


class CreateSectionRequest(CustomBaseModel):
    project_id: int
    name: str
    is_staged: bool = False
    session_id: str | None = None


class RenameSectionRequest(CustomBaseModel):
    section_id: int
    new_name: str
    is_staged: bool = False


class DeleteSectionRequest(CustomBaseModel):
    section_id: int
    is_staged: bool = False


class MoveTierGroupRequest(CustomBaseModel):
    tier_group_id: int
    section_id: int
    project_id: int
    tier_id: int
    tier_name: str
    is_staged: bool = False


class CreateTierGroupRequest(CustomBaseModel):
    section_id: int
    project_id: int
    tier_id: int
    tier_name: str
    is_staged: bool = False
