from sqlalchemy.orm import Session

from app.models.team import Team


def seed_database(db: Session) -> None:
    if db.query(Team).first():
        return

    team = Team(
        name="Rowing Club",
        description="Default club team",
        invite_code="ROWCREW",
    )
    db.add(team)
    db.commit()
