from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.workout import Workout, WorkoutSource, WorkoutSplit, WorkoutVisibility


def _to_seconds(tenths: int | None) -> float | None:
    if tenths is None:
        return None
    return tenths / 10.0


def _compute_split_500m(duration_s: float | None, distance_m: float | None) -> float | None:
    if duration_s and distance_m:
        return (duration_s / distance_m) * 500
    return None


def _parse_date(result: dict) -> datetime:
    raw = result.get("date_utc") or result.get("date")
    if isinstance(raw, str):
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return datetime.utcnow()


def _get_heart_rate(result: dict) -> int | None:
    hr = result.get("heart_rate") or {}
    return hr.get("average") if isinstance(hr, dict) else None


def _normalize_result(result: dict) -> dict:
    time_tenths = result.get("time")
    duration_seconds = _to_seconds(time_tenths)
    if duration_seconds is not None:
        duration_seconds = round(duration_seconds)
    distance_meters = result.get("distance")
    return {
        "source_id": str(result["id"]),
        "workout_date": _parse_date(result),
        "duration_seconds": duration_seconds,
        "distance_meters": distance_meters,
        "stroke_rate": result.get("stroke_rate"),
        "avg_heart_rate": _get_heart_rate(result),
        "avg_split_500m": _compute_split_500m(duration_seconds, distance_meters),
        "calories": result.get("calories_total"),
        "workout_name": result.get("workout_type"),
        "source": WorkoutSource.CONCEPT2,
        "visibility": WorkoutVisibility.PRIVATE,
    }


def _normalize_splits(result: dict) -> list[dict]:
    workout = result.get("workout") or {}
    raw_splits = workout.get("splits") or workout.get("intervals") or []
    normalized = []
    for i, split in enumerate(raw_splits):
        time_tenths = split.get("time")
        distance_m = split.get("distance")
        duration_s = _to_seconds(time_tenths)
        normalized.append({
            "split_number": i + 1,
            "distance_meters": distance_m,
            "duration_seconds": duration_s,
            "split_500m": _compute_split_500m(duration_s, distance_m) or split.get("split_500m"),
            "stroke_rate": split.get("stroke_rate"),
            "heart_rate": _get_heart_rate(split),
        })
    return normalized


def sync_concept2_results(
    db: Session,
    user_id: UUID,
    results: list[dict],
) -> dict:
    imported = 0
    updated = 0
    skipped = 0
    errors = []

    for result in results:
        try:
            source_id = str(result["id"])
            existing = (
                db.query(Workout)
                .filter(
                    Workout.user_id == user_id,
                    Workout.source == WorkoutSource.CONCEPT2,
                    Workout.source_id == source_id,
                )
                .first()
            )

            norm = _normalize_result(result)
            splits = _normalize_splits(result)

            if existing:
                for field, value in norm.items():
                    setattr(existing, field, value)
                db.flush()
                db.query(WorkoutSplit).filter(
                    WorkoutSplit.workout_id == existing.id
                ).delete()
                for s in splits:
                    db.add(WorkoutSplit(workout_id=existing.id, **s))
                updated += 1
            else:
                workout = Workout(user_id=user_id, **norm)
                db.add(workout)
                db.flush()
                for s in splits:
                    db.add(WorkoutSplit(workout_id=workout.id, **s))
                imported += 1
        except Exception as e:
            errors.append({"result_id": result.get("id"), "error": str(e)})

    db.commit()
    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
