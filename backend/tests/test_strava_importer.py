from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.workout import Workout, WorkoutSource, WorkoutVisibility
from app.services.strava_importer import sync_strava_activities

ROWING_ACTIVITY = {
    "id": 1001,
    "sport_type": "Rowing",
    "start_date": "2026-05-24T12:30:00Z",
    "name": "Morning Row",
    "moving_time": 1800,
    "distance": 5000.0,
    "average_heartrate": 155,
    "average_watts": 200.0,
    "calories": 350,
}

RUN_ACTIVITY = {
    "id": 2001,
    "sport_type": "Run",
    "start_date": "2026-05-24T14:00:00Z",
    "name": "Afternoon Run",
    "moving_time": 2400,
    "distance": 8000.0,
}

RIDE_ACTIVITY = {
    "id": 2002,
    "sport_type": "Ride",
    "start_date": "2026-05-25T10:00:00Z",
    "name": "Morning Ride",
    "elapsed_time": 3600,
    "distance": 30000.0,
}

SWIM_ACTIVITY = {
    "id": 2003,
    "sport_type": "Swim",
    "start_date": "2026-05-26T08:00:00Z",
    "name": "Pool Session",
    "moving_time": 2700,
    "distance": 2000.0,
}


class TestRowingOnlyFilter:
    def test_imports_rowing_activity(self, db: Session):
        user_id = uuid4()
        result = sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        assert result["imported"] == 1
        assert result["skipped"] == 0

        workout = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.source == WorkoutSource.STRAVA,
        ).first()
        assert workout is not None
        assert workout.source_id == "1001"

    def test_skips_non_rowing_activities(self, db: Session):
        user_id = uuid4()
        result = sync_strava_activities(db, user_id, [RUN_ACTIVITY, RIDE_ACTIVITY, SWIM_ACTIVITY])
        assert result["imported"] == 0
        assert result["skipped"] == 3

        count = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.source == WorkoutSource.STRAVA,
        ).count()
        assert count == 0

    def test_mixed_imports_only_rowing(self, db: Session):
        user_id = uuid4()
        activities = [ROWING_ACTIVITY, RUN_ACTIVITY, RIDE_ACTIVITY]
        result = sync_strava_activities(db, user_id, activities)
        assert result["imported"] == 1
        assert result["skipped"] == 2

    def test_no_fallback_to_deprecated_type(self, db: Session):
        user_id = uuid4()
        activity = {
            "id": 3001,
            "type": "Rowing",
            "sport_type": None,
            "start_date": "2026-05-24T12:00:00Z",
            "name": "No Sport Type",
            "moving_time": 1800,
            "distance": 5000.0,
        }
        result = sync_strava_activities(db, user_id, [activity])
        assert result["imported"] == 0
        assert result["skipped"] == 1


class TestNormalization:
    def test_source_strava(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.source == WorkoutSource.STRAVA

    def test_source_id_set(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.source_id == "1001"

    def test_visibility_private(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.visibility == WorkoutVisibility.PRIVATE

    def test_workout_name(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.workout_name == "Morning Row"

    def test_duration_moving_time_preferred(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.duration_seconds == 1800

    def test_duration_fallback_to_elapsed_time(self, db: Session):
        user_id = uuid4()
        activity = {
            "id": 4001,
            "sport_type": "Rowing",
            "start_date": "2026-05-24T12:00:00Z",
            "name": "No Moving Time",
            "elapsed_time": 2000,
            "distance": 5000.0,
        }
        sync_strava_activities(db, user_id, [activity])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.duration_seconds == 2000

    def test_distance_meters(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.distance_meters == 5000.0

    def test_avg_heart_rate(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.avg_heart_rate == 155

    def test_avg_heart_rate_normalizes_float_to_int(self, db: Session):
        user_id = uuid4()
        activity = dict(ROWING_ACTIVITY)
        activity["average_heartrate"] = 133.8
        sync_strava_activities(db, user_id, [activity])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.avg_heart_rate == 134
        assert isinstance(workout.avg_heart_rate, int)

    def test_avg_watts(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.avg_watts == 200.0

    def test_calories(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.calories == 350

    def test_avg_split_500m_computed(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        expected = (1800.0 / 5000.0) * 500
        assert workout.avg_split_500m == pytest.approx(expected, rel=1e-6)

    def test_workout_date_from_start_date(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.workout_date is not None

    def test_workout_date_fallback_start_date_local(self, db: Session):
        user_id = uuid4()
        activity = {
            "id": 5001,
            "sport_type": "Rowing",
            "start_date_local": "2026-05-24T08:00:00",
            "name": "Local Time Row",
            "moving_time": 1800,
            "distance": 5000.0,
        }
        sync_strava_activities(db, user_id, [activity])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.workout_date is not None

    def test_stroke_rate_not_set_by_default(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.stroke_rate is None


class TestUpsertIdempotent:
    def test_second_sync_does_not_create_duplicate(self, db: Session):
        user_id = uuid4()
        result1 = sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        assert result1["imported"] == 1
        assert result1["updated"] == 0

        result2 = sync_strava_activities(db, user_id, [ROWING_ACTIVITY])
        assert result2["imported"] == 0
        assert result2["updated"] == 1

        count = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.source == WorkoutSource.STRAVA,
        ).count()
        assert count == 1

    def test_upsert_updates_existing_fields(self, db: Session):
        user_id = uuid4()
        sync_strava_activities(db, user_id, [ROWING_ACTIVITY])

        modified = dict(ROWING_ACTIVITY)
        modified["calories"] = 400

        sync_strava_activities(db, user_id, [modified])
        workout = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.source_id == "1001",
        ).first()
        assert workout.calories == 400


class TestMultiUser:
    def test_different_users_get_separate_workouts(self, db: Session):
        user_a = uuid4()
        user_b = uuid4()
        sync_strava_activities(db, user_a, [ROWING_ACTIVITY])
        sync_strava_activities(db, user_b, [ROWING_ACTIVITY])

        count_a = db.query(Workout).filter(Workout.user_id == user_a).count()
        count_b = db.query(Workout).filter(Workout.user_id == user_b).count()
        assert count_a == 1
        assert count_b == 1
