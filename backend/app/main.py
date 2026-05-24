from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, workouts, teams
from app.seed import seed_database


def ensure_dev_workout_columns():
    """Apply tiny SQLite-only dev schema shims for existing local databases.

    The app does not have Alembic yet and development uses `create_all()`, which
    will not add columns to an already-created SQLite table. Keep this scoped to
    SQLite local dev so we do not mutate shared Postgres schemas outside a real
    migration path.
    """
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if not inspector.has_table("workouts"):
        return

    columns = {column["name"] for column in inspector.get_columns("workouts")}
    if "workout_name" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE workouts ADD COLUMN workout_name VARCHAR(120)"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only — use alembic in prod)
    if settings.environment == "development":
        Base.metadata.create_all(bind=engine)
        ensure_dev_workout_columns()
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title="Rowing Proj API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and mobile app (Tailscale)
configured_cors_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, *configured_cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(teams.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
