from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.workout import Workout, WorkoutSource, WorkoutSplit, WorkoutVisibility
from app.services.concept2_importer import sync_concept2_results


SAMPLE_RESULT = {
    "id": 98765,
    "date": "2026-05-24",
    "date_utc": "2026-05-24T12:30:00Z",
    "time": 18000,  # tenths of seconds -> 1800 seconds
    "distance": 5000,
    "stroke_rate": 24,
    "heart_rate": {"average": 155, "ending": 160},
    "calories_total": 350,
    "workout_type": "Steady State",
}

INTERVAL_RESULT = {
    "id": 98766,
    "date": "2026-05-24",
    "date_utc": "2026-05-24T14:00:00Z",
    "time": 21600,  # 2160 seconds
    "distance": 6000,
    "stroke_rate": 26,
    "heart_rate": {"average": 160},
    "calories_total": 420,
    "workout_type": "4x1500m",
    "workout": {
        "splits": [
            {"time": 5400, "distance": 1500, "stroke_rate": 26, "heart_rate": {"average": 158}},
            {"time": 5400, "distance": 1500, "stroke_rate": 27, "heart_rate": {"average": 162}},
            {"time": 5400, "distance": 1500, "stroke_rate": 26, "heart_rate": {"average": 161}},
            {"time": 5400, "distance": 1500, "stroke_rate": 26, "heart_rate": {"average": 163}},
        ],
    },
}

INTERVAL_RESULT_INTERVALS = {
    "id": 98767,
    "date": "2026-05-25",
    "date_utc": "2026-05-25T10:00:00Z",
    "time": 12000,
    "distance": 4000,
    "workout": {
        "intervals": [
            {"time": 6000, "distance": 2000, "stroke_rate": 28},
            {"time": 6000, "distance": 2000, "stroke_rate": 29},
        ],
    },
}


class TestNormalization:
    def test_time_tenths_converted_to_seconds(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout is not None
        assert workout.duration_seconds == 1800

    def test_fractional_tenths_duration_is_stored_as_whole_seconds(self, db: Session):
        user_id = uuid4()
        result = dict(SAMPLE_RESULT)
        result["id"] = 98768
        result["time"] = 3195  # 319.5 seconds from Concept2 tenths

        sync_concept2_results(db, user_id, [result])

        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout is not None
        assert workout.duration_seconds == 320

    def test_distance_meters(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.distance_meters == 5000

    def test_avg_split_500m_computed(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        expected = (1800.0 / 5000.0) * 500
        assert workout.avg_split_500m == pytest.approx(expected, rel=1e-6)

    def test_source_concept2(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.source == WorkoutSource.CONCEPT2

    def test_source_id_set(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.source_id == "98765"

    def test_visibility_private(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.visibility == WorkoutVisibility.PRIVATE

    def test_heart_rate_average(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.avg_heart_rate == 155

    def test_calories(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.calories == 350

    def test_workout_name(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.workout_name == "Steady State"

    def test_stroke_rate(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        assert workout.stroke_rate == 24


class TestUpsertIdempotent:
    def test_second_sync_does_not_create_duplicate(self, db: Session):
        user_id = uuid4()
        result1 = sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        assert result1["imported"] == 1
        assert result1["updated"] == 0

        result2 = sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        assert result2["imported"] == 0
        assert result2["updated"] == 1

        count = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.source == WorkoutSource.CONCEPT2,
        ).count()
        assert count == 1

    def test_upsert_updates_existing_fields(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])

        modified = dict(SAMPLE_RESULT)
        modified["calories_total"] = 400

        sync_concept2_results(db, user_id, [modified])
        workout = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.source_id == "98765",
        ).first()
        assert workout.calories == 400


class TestSplits:
    def test_splits_are_stored(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [INTERVAL_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        splits = db.query(WorkoutSplit).filter(WorkoutSplit.workout_id == workout.id).order_by(WorkoutSplit.split_number).all()
        assert len(splits) == 4
        assert splits[0].split_number == 1
        assert splits[0].distance_meters == 1500
        assert splits[0].duration_seconds == 540.0
        assert splits[0].stroke_rate == 26
        assert splits[0].heart_rate == 158

    def test_splits_replaced_on_update(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [INTERVAL_RESULT])

        modified = dict(INTERVAL_RESULT)
        modified["workout"] = {
            "splits": [
                {"time": 7200, "distance": 2000, "stroke_rate": 28, "heart_rate": {"average": 170}},
            ],
        }

        sync_concept2_results(db, user_id, [modified])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        splits = db.query(WorkoutSplit).filter(WorkoutSplit.workout_id == workout.id).all()
        assert len(splits) == 1
        assert splits[0].distance_meters == 2000
        assert splits[0].split_number == 1

    def test_intervals_stored_as_splits(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [INTERVAL_RESULT_INTERVALS])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        splits = db.query(WorkoutSplit).filter(WorkoutSplit.workout_id == workout.id).order_by(WorkoutSplit.split_number).all()
        assert len(splits) == 2
        assert splits[0].distance_meters == 2000
        assert splits[0].duration_seconds == 600.0
        assert splits[0].stroke_rate == 28

    def test_no_splits_when_none_in_payload(self, db: Session):
        user_id = uuid4()
        sync_concept2_results(db, user_id, [SAMPLE_RESULT])
        workout = db.query(Workout).filter(Workout.user_id == user_id).first()
        splits = db.query(WorkoutSplit).filter(WorkoutSplit.workout_id == workout.id).all()
        assert len(splits) == 0


class TestMultiUser:
    def test_different_users_get_separate_workouts(self, db: Session):
        user_a = uuid4()
        user_b = uuid4()
        sync_concept2_results(db, user_a, [SAMPLE_RESULT])
        sync_concept2_results(db, user_b, [SAMPLE_RESULT])

        count_a = db.query(Workout).filter(Workout.user_id == user_a).count()
        count_b = db.query(Workout).filter(Workout.user_id == user_b).count()
        assert count_a == 1
        assert count_b == 1
