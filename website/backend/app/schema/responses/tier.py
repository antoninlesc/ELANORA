from app.schema.common.base import CustomBaseModel
from typing import List, Optional, Dict
from pydantic import Field


class TierNode(CustomBaseModel):
    tier_id: int
    tier_name: str
    parent_tier_id: Optional[int] = None
    children: List["TierNode"] = Field(default_factory=list)


TierNode.model_rebuild()


class TierTreeResponse(CustomBaseModel):
    tiers: Dict[str, List[TierNode]]


from typing import List, Dict, Optional
from pydantic import BaseModel


class SectionInfo(CustomBaseModel):
    section_id: int
    name: str


class TierGroupInfo(CustomBaseModel):
    tier_group_id: int
    elan_file_name: str
    section_id: Optional[int]
    tiers: List[TierNode] = []


class SectionsAndGroupsResponse(CustomBaseModel):
    sections: List[SectionInfo]
    tier_groups: List[TierGroupInfo]
