from pydantic import BaseModel


class TierTreeRequest(BaseModel):
    project_name: str
