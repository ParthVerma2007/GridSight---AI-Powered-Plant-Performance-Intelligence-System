from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.plant import Plant, Asset
from app.models.equipment import EquipmentTelemetry
from app.auth.rbac import get_current_role, UserRole
from app.config import settings

router = APIRouter(prefix="/plant", tags=["Plant & Assets"])

@router.get("/details")
def get_plant_details(
    plant_id: str = "helios-50",
    db: Session = Depends(get_db)
):
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")

    asset_count = db.query(Asset).filter(Asset.plant_id == plant_id).count()
    return {
        "id": plant.id,
        "name": plant.name,
        "capacity_mw": plant.capacity_mw,
        "technology": plant.technology,
        "latitude": plant.latitude,
        "longitude": plant.longitude,
        "timezone": plant.timezone,
        "commissioned_date": plant.commissioned_date.isoformat(),
        "total_assets": asset_count
    }

@router.get("/assets")
def list_assets(
    plant_id: str = "helios-50",
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Asset).filter(Asset.plant_id == plant_id)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    assets = query.order_by(Asset.id).all()

    return [{
        "id": a.id,
        "name": a.name,
        "asset_type": a.asset_type,
        "capacity_kw": a.capacity_kw,
        "model": a.model,
        "status": a.status
    } for a in assets]

@router.get("/assets/{asset_id}/history")
def get_asset_history(
    asset_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Returns recent telemetry time series, alarms, and operating states for a specific asset.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    latest_telem = db.query(EquipmentTelemetry).filter(
        EquipmentTelemetry.asset_id == asset_id
    ).order_by(EquipmentTelemetry.timestamp.desc()).first()

    if not latest_telem:
        return {"asset_id": asset_id, "telemetry": [], "recent_alarms": []}

    end_time = latest_telem.timestamp
    start_time = end_time - timedelta(hours=hours)

    records = db.query(EquipmentTelemetry).filter(
        EquipmentTelemetry.asset_id == asset_id,
        EquipmentTelemetry.timestamp >= start_time,
        EquipmentTelemetry.timestamp <= end_time
    ).order_by(EquipmentTelemetry.timestamp.asc()).all()

    telemetry_data = [{
        "timestamp": r.timestamp.isoformat(),
        "ac_power_kw": r.ac_power_kw,
        "dc_power_kw": r.dc_power_kw,
        "dc_voltage_v": r.dc_voltage_v,
        "dc_current_a": r.dc_current_a,
        "inverter_temp_c": r.inverter_temp_c,
        "efficiency_pct": r.efficiency_pct,
        "operating_state": r.operating_state,
        "alarm_code": r.alarm_code
    } for r in records]

    alarms = [{
        "timestamp": r.timestamp.isoformat(),
        "alarm_code": r.alarm_code,
        "alarm_description": r.alarm_description,
        "inverter_temp_c": r.inverter_temp_c
    } for r in records if r.alarm_code]

    return {
        "asset_id": asset_id,
        "name": asset.name,
        "status": asset.status,
        "telemetry_points": len(telemetry_data),
        "telemetry": telemetry_data,
        "recent_alarms": alarms
    }
