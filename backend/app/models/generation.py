from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

class GenerationRecord(Base):
    __tablename__ = "generation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    asset_id = Column(String(64), ForeignKey("assets.id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    actual_mw = Column(Float, nullable=False)
    actual_mwh = Column(Float, nullable=False)
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plant_id", "asset_id", "timestamp", name="uq_generation_asset_time"),
    )
