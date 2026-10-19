from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from datetime import datetime
from app.database import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_number = Column(String(64), unique=True, nullable=False, index=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    asset_id = Column(String(64), ForeignKey("assets.id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(32), default="P2_HIGH")  # P1_CRITICAL, P2_HIGH, P3_NORMAL
    status = Column(String(32), default="assigned")   # assigned, in_progress, waiting_parts, completed
    assigned_technician = Column(String(128), nullable=False)
    estimated_hours = Column(Float, default=2.5)
    actual_hours = Column(Float, nullable=True)
    procedure_code = Column(String(64), default="SOP-INV-02")
    safety_interlock_verified = Column(Boolean, default=False)
    loto_applied = Column(Boolean, default=False)  # Lockout / Tagout isolation
    ai_troubleshooting_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
