from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

class ForecastRecord(Base):
    __tablename__ = "forecast_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    forecast_version = Column(String(64), nullable=False, index=True)  # e.g., 'day_ahead_v1', 'month_ahead_v1'
    forecast_horizon = Column(String(32), nullable=False, default="day_ahead")  # day_ahead, intraday, month_ahead
    forecast_generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    target_timestamp = Column(DateTime, nullable=False, index=True)
    expected_mw = Column(Float, nullable=False)
    expected_mwh = Column(Float, nullable=False)
    ghi_expected_wm2 = Column(Float, nullable=True)
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plant_id", "forecast_version", "target_timestamp", name="uq_forecast_version_target"),
    )
