from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Concept2StatusResponse(BaseModel):
    connected: bool
    concept2_user_id: str | None = None
    last_sync_at: datetime | None = None
    token_expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class Concept2ConnectResponse(BaseModel):
    authorization_url: str


class Concept2SyncResponse(BaseModel):
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[dict] = Field(default_factory=list)
