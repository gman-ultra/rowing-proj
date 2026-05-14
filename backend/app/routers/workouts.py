from fastapi import APIRouter

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


@router.get("")
def list_workouts():
    return {"workouts": []}


@router.post("")
def create_workout():
    return {"message": "Not implemented yet"}
