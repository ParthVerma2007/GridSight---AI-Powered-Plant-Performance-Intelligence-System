from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from datetime import datetime
from app.database import Base

class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), unique=True, nullable=False, index=True)
    source_file = Column(String(256), nullable=False)
    file_type = Column(String(64), nullable=False)  # generation, forecast, equipment, weather, etc.
    total_records = Column(Integer, default=0)
    valid_records = Column(Integer, default=0)
    quarantined_records = Column(Integer, default=0)
    status = Column(String(32), default="completed")  # completed, partial, failed
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuarantineRecord(Base):
    __tablename__ = "quarantine_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False, index=True)
    source_file = Column(String(256), nullable=False)
    row_index = Column(Integer, nullable=False)
    raw_content = Column(Text, nullable=False)
    error_type = Column(String(64), nullable=False)  # validation_error, duplicate_conflict, unit_error, malformed
    error_detail = Column(Text, nullable=False)
    quarantined_at = Column(DateTime, default=datetime.utcnow)
