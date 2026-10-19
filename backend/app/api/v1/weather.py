from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.database import get_db
from app.models.weather import WeatherRecord
from app.weather.open_meteo import OpenMeteoClient
from app.api.v1.analytics import get_default_time_range
from app.auth.rbac import get_current_role, UserRole

router = APIRouter(prefix="/weather", tags=["Weather Integration"])

@router.get("/history", response_model=List[dict])
def get_weather_history(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    data_type: Optional[str] = Query(None),  # observed, forecast, estimated
    db: Session = Depends(get_db)
):
    """
    Returns weather time series distinguishing observed, forecast, and estimated values.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    query = db.query(WeatherRecord).filter(
        WeatherRecord.plant_id == plant_id,
        WeatherRecord.timestamp >= start_time,
        WeatherRecord.timestamp <= end_time
    )
    if data_type:
        query = query.filter(WeatherRecord.data_type == data_type)
    records = query.order_by(WeatherRecord.timestamp.asc()).all()

    return [{
        "timestamp": r.timestamp.isoformat(),
        "ghi_wm2": r.ghi_wm2,
        "dni_wm2": r.dni_wm2,
        "dhi_wm2": r.dhi_wm2,
        "ambient_temp_c": r.ambient_temp_c,
        "cell_temp_c": r.cell_temp_c,
        "wind_speed_ms": r.wind_speed_ms,
        "cloud_cover_pct": r.cloud_cover_pct,
        "data_type": r.data_type,
        "source_provider": r.source_provider,
        "provenance_notes": r.provenance_notes
    } for r in records]

@router.post("/sync", response_model=dict)
async def sync_weather_with_open_meteo(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    plant_id: str = "helios-50",
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    """
    Syncs solar irradiance and ambient weather metrics from Open-Meteo API.
    """
    if not end_date:
        end_date = datetime.utcnow().date()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    client = OpenMeteoClient(db, plant_id)
    records = await client.fetch_and_cache_weather(start_date, end_date)

    return {
        "message": f"Synchronized weather for {plant_id} from {start_date} to {end_date}",
        "records_count": len(records),
        "cached": True
    }
