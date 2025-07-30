from app.schema.common.base import CustomBaseModel
from typing import List, Optional


class TierNode(CustomBaseModel):
    tier_id: int
    tier_name: str
    parent_tier_id: Optional[int] = None
    children: List["TierNode"] = []


TierNode.model_rebuild()


class TierTreeResponse(CustomBaseModel):
    tiers: List[TierNode]
