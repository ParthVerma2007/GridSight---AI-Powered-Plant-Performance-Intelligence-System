from fastapi import APIRouter
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.plant import router as plant_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.attribution import router as attribution_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.investigations import router as investigations_router
from app.api.v1.work_orders import router as work_orders_router
from app.api.v1.weather import router as weather_router
from app.api.v1.ai import router as ai_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(plant_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(attribution_router)
api_v1_router.include_router(dashboards_router)
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(work_orders_router)
api_v1_router.include_router(weather_router)
api_v1_router.include_router(ai_router)
