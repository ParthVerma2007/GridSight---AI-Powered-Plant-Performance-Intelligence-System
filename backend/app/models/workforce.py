from sqlalchemy import Column, String, Float, DateTime, Integer, Date, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

class WorkforceRecord(Base):
    __tablename__ = "workforce_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    shift = Column(String(32), nullable=False)  # morning, afternoon, night
    technicians_on_site = Column(Integer, nullable=False, default=2)
    hours_logged = Column(Float, nullable=False, default=8.0)
    lead_technician = Column(String(128), nullable=False)
    technician_roster = Column(String(256), nullable=True)
    skill_certifications = Column(String(256), default="HV_Certified, Inverter_Specialist")
    notes = Column(String(512), nullable=True)
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plant_id", "date", "shift", name="uq_workforce_plant_date_shift"),
    )
