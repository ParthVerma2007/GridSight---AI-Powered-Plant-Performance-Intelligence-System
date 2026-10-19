from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.attribution.engine import VarianceAttributionEngine
from app.schemas.attribution import VarianceAttributionReport
from app.api.v1.analytics import get_default_time_range
from app.auth.rbac import get_current_role, UserRole

router = APIRouter(prefix="/attribution", tags=["Variance Attribution"])

@router.get("/report", response_model=VarianceAttributionReport)
def get_variance_attribution_report(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    """
    Returns cause-based variance attribution report with double-counting prevention,
    mathematical reconciliation proof, and evidence citations.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    engine = VarianceAttributionEngine(db, plant_id)
    return engine.attribute_variance(start_time, end_time, forecast_version)
