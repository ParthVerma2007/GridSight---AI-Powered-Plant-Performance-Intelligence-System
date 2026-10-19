from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from datetime import datetime
from app.database import Base

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    work_order_id = Column(String(64), nullable=False, index=True)
    asset_id = Column(String(64), ForeignKey("assets.id"), nullable=False, index=True)
    maintenance_type = Column(String(32), nullable=False)  # corrective, preventative, inspection
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    downtime_hours = Column(Float, default=0.0)
    technician_in_charge = Column(String(128), nullable=False)
    procedure_code = Column(String(64), default="SOP-ELEC-04")
    procedure_description = Column(String(256), nullable=True)
    status = Column(String(32), default="scheduled")  # scheduled, in_progress, completed, deferred
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
