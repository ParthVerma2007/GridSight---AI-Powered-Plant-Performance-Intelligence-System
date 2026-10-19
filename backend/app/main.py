import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.v1 import api_v1_router
from app.ingestion.pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("plant_intelligence")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Initialize default plant & assets
    db = SessionLocal()
    try:
        pipeline = IngestionPipeline(db)
        plant = pipeline.ensure_default_plant_and_assets(settings.PLANT_ID)
        logger.info(f"Initialized plant: {plant.name} ({plant.capacity_mw} MW)")
    finally:
        db.close()

    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="AI-Powered Plant Performance Intelligence System",
    description="Deterministic analytics, cause-based variance attribution, and role-specific intelligence for energy plants.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Vite dev server & production frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_v1_router)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "system": "Plant Performance Intelligence System",
        "plant_id": settings.PLANT_ID,
        "capacity_mw": settings.PLANT_CAPACITY_MW,
        "ai_provider": settings.AI_PROVIDER
    }
