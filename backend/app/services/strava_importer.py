from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.workout import Workout, WorkoutSource, WorkoutVisibility


def _get_activity_date(activity: dict) -> datetime:
    raw = activity.get("start_date") or activity.get("start_date_local")
    if isinstance(raw, str):
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return datetime.utcnow()


def _compute_split_500m(duration_s: float | None, distance_m: float | None) -> float | None:
    if duration_s and distance_m and distance_m > 0:
        return (duration_s / distance_m) * 500
    return None


def _normalize_heart_rate(raw_heart_rate) -> int | None:
    if raw_heart_rate is None:
        return None
    return round(raw_heart_rate)


def _normalize_activity(activity: dict) -> dict:
    duration_seconds = activity.get("moving_time") or activity.get("elapsed_time")
    distance_meters = activity.get("distance")
    return {
        "source_id": str(activity["id"]),
        "workout_date": _get_activity_date(activity),
        "workout_name": activity.get("name"),
        "duration_seconds": duration_seconds,
        "distance_meters": distance_meters,
        "avg_heart_rate": _normalize_heart_rate(activity.get("average_heartrate")),
        "avg_watts": activity.get("average_watts"),
        "calories": activity.get("calories"),
        "avg_split_500m": _compute_split_500m(duration_seconds, distance_meters),
        "source": WorkoutSource.STRAVA,
        "visibility": WorkoutVisibility.PRIVATE,
    }


def sync_strava_activities(
    db: Session,
    user_id: UUID,
    activities: list[dict],
) -> dict:
    imported = 0
    updated = 0
    skipped = 0
    errors = []

    for activity in activities:
        try:
            sport_type = activity.get("sport_type")
            if sport_type != "Rowing":
                skipped += 1
                continue

            source_id = str(activity["id"])
            existing = (
                db.query(Workout)
                .filter(
                    Workout.user_id == user_id,
                    Workout.source == WorkoutSource.STRAVA,
                    Workout.source_id == source_id,
                )
                .first()
            )

            norm = _normalize_activity(activity)

            if existing:
                for field, value in norm.items():
                    setattr(existing, field, value)
                updated += 1
            else:
                workout = Workout(user_id=user_id, **norm)
                db.add(workout)
                imported += 1
        except Exception as e:
            errors.append({"activity_id": activity.get("id"), "error": str(e)})

    db.commit()
    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
