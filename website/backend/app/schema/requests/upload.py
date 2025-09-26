from app.schema.common.base import CustomBaseModel


class ProcessUploadRequest(CustomBaseModel):
    project_id: int


class ConfirmUploadRequest(CustomBaseModel):
    session_id: str
    tier_assignments: list[
        dict
    ]  # List of {"tier_name": str, "section_name": str, "parent_tier_name": str | None}
    new_section_names: list[str]
    description: str


class CancelUploadRequest(CustomBaseModel):
    session_id: str
