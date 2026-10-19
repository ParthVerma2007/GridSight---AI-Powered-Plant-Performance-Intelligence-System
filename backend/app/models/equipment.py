from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

class EquipmentTelemetry(Base):
    __tablename__ = "equipment_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(64), ForeignKey("assets.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    dc_power_kw = Column(Float, nullable=True)
    ac_power_kw = Column(Float, nullable=True)
    dc_voltage_v = Column(Float, nullable=True)
    dc_current_a = Column(Float, nullable=True)
    inverter_temp_c = Column(Float, nullable=True)
    efficiency_pct = Column(Float, nullable=True)
    operating_state = Column(String(32), default="running")  # running, derated, fault_trip, standby, offline
    alarm_code = Column(String(64), nullable=True)
    alarm_description = Column(String(256), nullable=True)
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("asset_id", "timestamp", name="uq_equipment_telemetry_time"),
    )
