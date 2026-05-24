from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


class WorkoutCreate(BaseModel):
    team_id: UUID | None = None
    workout_date: datetime | None = None
    workout_name: str | None = Field(None, max_length=120)
    duration_seconds: int = Field(..., gt=0, description="Duration in seconds (positive integer)")
    distance_meters: float = Field(..., gt=0, description="Distance in meters (positive number)")
    stroke_rate: float | None = Field(None, gt=0)
    avg_heart_rate: int | None = Field(None, gt=0, le=250)
    avg_watts: float | None = Field(None, gt=0)
    calories: int | None = Field(None, gt=0)
    notes: str | None = Field(None, max_length=5000)
    visibility: str = Field(default="private", pattern=r"^(private|team)$")

    @field_validator("workout_name", mode="before")
    @classmethod
    def normalize_workout_name(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            value = v.strip()
            return value or None
        return v


class WorkoutUpdate(BaseModel):
    team_id: UUID | None = None
    workout_date: datetime | None = None
    workout_name: str | None = Field(None, max_length=120)
    duration_seconds: int | None = Field(None, gt=0, description="Duration in seconds (positive integer)")
    distance_meters: float | None = Field(None, gt=0, description="Distance in meters (positive number)")
    stroke_rate: float | None = Field(None, gt=0)
    avg_heart_rate: int | None = Field(None, gt=0, le=250)
    avg_watts: float | None = Field(None, gt=0)
    calories: int | None = Field(None, gt=0)
    notes: str | None = Field(None, max_length=5000)
    visibility: str | None = Field(None, pattern=r"^(private|team)$")

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data):
        if isinstance(data, dict):
            for field in ("workout_date", "duration_seconds", "distance_meters", "visibility"):
                if data.get(field, "__missing__") is None:
                    raise ValueError(f"{field} cannot be null")
        return data

    @field_validator("workout_name", mode="before")
    @classmethod
    def normalize_workout_name(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            value = v.strip()
            return value or None
        return v


class WorkoutOut(BaseModel):
    id: UUID
    user_id: UUID
    team_id: UUID | None
    workout_date: datetime
    workout_name: str | None
    duration_seconds: int | None
    distance_meters: float | None
    stroke_rate: float | None
    avg_split_500m: float | None
    avg_heart_rate: int | None
    avg_watts: float | None
    calories: int | None
    notes: str | None
    source: str
    source_id: str | None
    visibility: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkoutListResponse(BaseModel):
    workouts: list[WorkoutOut]
