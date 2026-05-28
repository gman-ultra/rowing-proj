from datetime import datetime

from pydantic import BaseModel, Field


class StravaStatusResponse(BaseModel):
    connected: bool
    strava_athlete_id: str | None = None
    last_sync_at: datetime | None = None
    token_expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class StravaConnectResponse(BaseModel):
    authorization_url: str


class StravaSyncResponse(BaseModel):
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[dict] = Field(default_factory=list)
