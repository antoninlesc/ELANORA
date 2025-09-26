from app.schema.common.base import CustomBaseModel


class ProcessUploadResponse(CustomBaseModel):
    session_id: str
    extracted_tiers: list[dict]


class ConfirmUploadResponse(CustomBaseModel):
    message: str


class CancelUploadResponse(CustomBaseModel):
    message: str


class CleanupExpiredResponse(CustomBaseModel):
    message: str
    cleaned_count: int
