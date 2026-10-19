from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    ghi_wm2 = Column(Float, nullable=True)          # Global Horizontal Irradiance (W/m2)
    dni_wm2 = Column(Float, nullable=True)          # Direct Normal Irradiance (W/m2)
    dhi_wm2 = Column(Float, nullable=True)          # Diffuse Horizontal Irradiance (W/m2)
    ambient_temp_c = Column(Float, nullable=True)   # Ambient Temperature (Celsius)
    cell_temp_c = Column(Float, nullable=True)      # PV Cell Temperature (Celsius)
    wind_speed_ms = Column(Float, nullable=True)    # Wind Speed (m/s)
    cloud_cover_pct = Column(Float, nullable=True)  # Cloud Cover (%)
    data_type = Column(String(32), nullable=False)  # 'observed', 'forecast', 'estimated', 'unavailable'
    source_provider = Column(String(64), default="open-meteo")
    provenance_notes = Column(String(256), nullable=True)
    source_file = Column(String(256), nullable=True)
    source_row_index = Column(Integer, nullable=True)
    ingestion_batch_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plant_id", "timestamp", "data_type", name="uq_weather_plant_time_type"),
    )
