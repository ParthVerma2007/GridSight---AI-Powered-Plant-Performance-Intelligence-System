from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.schemas.analytics import KPISummary, TimeSeriesPoint, DailyPerformanceItem
from app.auth.rbac import get_current_role, UserRole
from app.models.generation import GenerationRecord

router = APIRouter(prefix="/analytics", tags=["Deterministic Analytics"])

def get_default_time_range(db: Session, plant_id: str = "helios-50"):
    """
    Finds the latest timestamp in the generation table or defaults to current date.
    """
    latest = db.query(GenerationRecord.timestamp).filter(
        GenerationRecord.plant_id == plant_id
    ).order_by(GenerationRecord.timestamp.desc()).first()

    if latest and latest[0]:
        end_time = latest[0]
        start_time = end_time - timedelta(days=7)
        return start_time, end_time

    end = datetime.utcnow()
    start = end - timedelta(days=7)
    return start, end

@router.get("/kpi", response_model=KPISummary)
def get_kpis(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    """
    Returns deterministic plant KPIs (Capacity factor, availability, variance, financial impact).
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    engine = DeterministicAnalyticsEngine(db, plant_id)
    return engine.compute_kpis(start_time, end_time, forecast_version)

@router.get("/timeseries", response_model=List[TimeSeriesPoint])
def get_timeseries(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db)
):
    """
    Returns aligned hourly expected MW, actual MW, variance MW, and GHI.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    engine = DeterministicAnalyticsEngine(db, plant_id)
    return engine.get_time_series(start_time, end_time, forecast_version)

@router.get("/daily", response_model=List[DailyPerformanceItem])
def get_daily_rollup(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db)
):
    """
    Returns daily aggregated generation, variance, availability, and financial impact.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    engine = DeterministicAnalyticsEngine(db, plant_id)
    return engine.get_daily_performance(start_time, end_time, forecast_version)
