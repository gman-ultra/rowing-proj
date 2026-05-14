from fastapi import APIRouter

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("")
def list_teams():
    return {"teams": []}


@router.post("")
def create_team():
    return {"message": "Not implemented yet"}
