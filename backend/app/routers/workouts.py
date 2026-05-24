from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.team import TeamMember
from app.models.user import User
from app.models.workout import Workout, WorkoutSource, WorkoutVisibility
from app.schemas.workout import WorkoutCreate, WorkoutListResponse, WorkoutOut, WorkoutUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


def _get_owned_workout(db: Session, workout_id: UUID, current_user: User) -> Workout:
    workout = (
        db.query(Workout)
        .filter(Workout.id == workout_id, Workout.user_id == current_user.id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


def _require_valid_team_membership(db: Session, current_user: User, team_id):
    if team_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team visibility requires choosing a team.",
        )

    membership = (
        db.query(TeamMember)
        .filter(
            TeamMember.user_id == current_user.id,
            TeamMember.team_id == team_id,
            TeamMember.is_active == True,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not a member of any team. Team visibility is unavailable.",
        )


def _compute_avg_split(duration_seconds, distance_meters):
    if duration_seconds and distance_meters:
        return (duration_seconds / distance_meters) * 500
    return None


@router.post("", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
def create_workout(
    body: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.visibility == "team":
        _require_valid_team_membership(db, current_user, body.team_id)

    workout = Workout(
        user_id=current_user.id,
        team_id=body.team_id if body.visibility == "team" else None,
        workout_date=body.workout_date or datetime.utcnow(),
        workout_name=body.workout_name,
        duration_seconds=body.duration_seconds,
        distance_meters=body.distance_meters,
        stroke_rate=body.stroke_rate,
        avg_split_500m=_compute_avg_split(body.duration_seconds, body.distance_meters),
        avg_heart_rate=body.avg_heart_rate,
        avg_watts=body.avg_watts,
        calories=body.calories,
        notes=body.notes,
        source=WorkoutSource.MANUAL,
        source_id=None,
        visibility=WorkoutVisibility(body.visibility),
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


@router.get("", response_model=WorkoutListResponse)
def list_workouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workouts = (
        db.query(Workout)
        .filter(Workout.user_id == current_user.id)
        .order_by(Workout.workout_date.desc())
        .all()
    )
    return WorkoutListResponse(workouts=workouts)


@router.get("/{workout_id}", response_model=WorkoutOut)
def get_workout(
    workout_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_workout(db, workout_id, current_user)


@router.patch("/{workout_id}", response_model=WorkoutOut)
def update_workout(
    workout_id: UUID,
    body: WorkoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workout = _get_owned_workout(db, workout_id, current_user)
    updates = body.model_dump(exclude_unset=True)

    next_visibility = updates.get("visibility", workout.visibility.value)
    next_team_id = updates["team_id"] if "team_id" in updates else workout.team_id

    if next_visibility == "team":
        _require_valid_team_membership(db, current_user, next_team_id)
    elif next_visibility == "private":
        next_team_id = None

    for field, value in updates.items():
        setattr(workout, field, value)

    workout.visibility = WorkoutVisibility(next_visibility)
    workout.team_id = next_team_id
    workout.avg_split_500m = _compute_avg_split(
        updates.get("duration_seconds", workout.duration_seconds),
        updates.get("distance_meters", workout.distance_meters),
    )

    db.commit()
    db.refresh(workout)
    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workout = _get_owned_workout(db, workout_id, current_user)
    db.delete(workout)
    db.commit()
