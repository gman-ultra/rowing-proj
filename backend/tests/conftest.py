import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.models.integration import Concept2Connection, OAuthState, StravaConnection
from app.services.auth import create_access_token, get_password_hash

TEST_DB = os.environ.get("TEST_DB_URL", "sqlite:///./test_rowing_proj.db")
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def team(db: Session) -> Team:
    team = Team(
        id=uuid4(),
        name="Test Crew",
        description="Test team",
        invite_code="TESTCREW",
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@pytest.fixture
def user_on_team(db: Session, team: Team) -> User:
    user = User(
        id=uuid4(),
        email="rower@test.com",
        hashed_password=get_password_hash("password123"),
        display_name="Test Rower",
    )
    db.add(user)
    db.flush()
    member = TeamMember(
        id=uuid4(),
        team_id=team.id,
        user_id=user.id,
        role=TeamRole.ATHLETE,
    )
    db.add(member)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_no_team(db: Session) -> User:
    user = User(
        id=uuid4(),
        email="loner@test.com",
        hashed_password=get_password_hash("password123"),
        display_name="Lone Rower",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token_headers(user_on_team: User) -> dict:
    token = create_access_token(user_on_team.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def token_headers_no_team(user_no_team: User) -> dict:
    token = create_access_token(user_no_team.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_workout_data() -> dict:
    return {
        "duration_seconds": 1800,
        "distance_meters": 5000.0,
        "stroke_rate": 24,
        "avg_heart_rate": 155,
        "avg_watts": 200.0,
        "calories": 350,
        "notes": "Good session",
    }
