from pydantic import Field

from app.schema.common.base import CustomBaseModel


class TierNode(CustomBaseModel):
    tier_id: int
    tier_name: str
    parent_tier_id: int | None = None
    children: list["TierNode"] = Field(default_factory=list)


TierNode.model_rebuild()


class TierTreeResponse(CustomBaseModel):
    tiers: dict[str, list[TierNode]]


class SectionInfo(CustomBaseModel):
    section_id: int
    name: str
    is_staged: bool | None = None
    session_id: str | None = None


class TierGroupInfo(CustomBaseModel):
    tier_group_id: int | None
    tier_name: str
    section_id: int | None = None
    tier_id: int
    parent_tier_id: int | None = None
    file_name: str | None = None


class SectionsAndGroupsResponse(CustomBaseModel):
    sections: list[SectionInfo]
    tier_groups: list[TierGroupInfo]
