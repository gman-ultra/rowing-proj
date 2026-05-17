from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, workouts, teams
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only — use alembic in prod)
    if settings.environment == "development":
        Base.metadata.create_all(bind=engine)
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

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
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
