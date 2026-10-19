from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from datetime import datetime
from app.database import Base

class ExternalEvent(Base):
    __tablename__ = "external_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    timestamp_start = Column(DateTime, nullable=False, index=True)
    timestamp_end = Column(DateTime, nullable=False)
    event_type = Column(String(64), nullable=False)  # grid_curtailment, frequency_excursion, transmission_outage
    curtailed_capacity_mw = Column(Float, default=0.0)
    iso_directive_code = Column(String(64), nullable=True)  # e.g., CAISO-DIR-9921
    compensation_eligible = Column(String(16), default="YES")
    impact_description = Column(String(256), nullable=True)
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
