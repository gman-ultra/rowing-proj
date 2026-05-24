import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

import enum


class WorkoutSource(str, enum.Enum):
    MANUAL = "manual"
    CONCEPT2 = "concept2"
    STRAVA = "strava"


class WorkoutVisibility(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)

    # Core workout data
    workout_date = Column(DateTime, nullable=False)
    workout_name = Column(String(120), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    distance_meters = Column(Float, nullable=True)
    stroke_rate = Column(Float, nullable=True)      # average strokes/min
    avg_split_500m = Column(Float, nullable=True)   # seconds per 500m
    avg_heart_rate = Column(Integer, nullable=True)
    avg_watts = Column(Float, nullable=True)
    calories = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Source tracking
    source = Column(Enum(WorkoutSource), nullable=False)
    source_id = Column(String(255), nullable=True)  # external ID (Strava activity ID, Concept2 logbook ID)
    visibility = Column(Enum(WorkoutVisibility), default=WorkoutVisibility.PRIVATE)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkoutSplit(Base):
    """Stores interval/split data for Concept2 detailed logs."""
    __tablename__ = "workout_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id"), nullable=False)
    split_number = Column(Integer, nullable=False)
    distance_meters = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    split_500m = Column(Float, nullable=True)
    stroke_rate = Column(Float, nullable=True)
    heart_rate = Column(Integer, nullable=True)
