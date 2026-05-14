from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
def get_current_user():
    return {"message": "Not implemented yet"}
