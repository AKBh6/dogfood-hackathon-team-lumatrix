from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.seed import seed_offline_fixtures

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs DB setup & preloads fixture data for zero-config offline runs
    init_db()
    seed_offline_fixtures()
    print("Dogfood Engine initialized: Database ready & Fixture data seeded.")
    yield
    print("Dogfood Engine shutting down...")
