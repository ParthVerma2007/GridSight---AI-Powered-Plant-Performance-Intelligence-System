from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from datetime import datetime
from app.database import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    cause_id = Column(String(64), nullable=True, index=True)  # link to attributed cause ID
    title = Column(String(256), nullable=False)
    cause_category = Column(String(64), nullable=False)  # equipment_fault, weather, grid_curtailment, maintenance
    description = Column(Text, nullable=True)
    owner = Column(String(128), nullable=False)
    status = Column(String(32), default="open")  # open, in_progress, resolved, closed
    priority = Column(String(32), default="medium")  # low, medium, high, critical
    controllability = Column(String(32), default="controllable")  # controllable, semi-controllable, uncontrollable
    recurrence_flag = Column(Boolean, default=False)
    deadline = Column(DateTime, nullable=True)
    action_plan = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
