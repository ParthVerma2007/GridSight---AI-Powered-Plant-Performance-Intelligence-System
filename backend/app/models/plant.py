from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Plant(Base):
    __tablename__ = "plants"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    capacity_mw = Column(Float, nullable=False, default=50.0)
    technology = Column(String(64), default="solar_pv")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(64), default="America/Los_Angeles")
    commissioned_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    assets = relationship("Asset", back_populates="plant", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(64), primary_key=True, index=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    asset_type = Column(String(64), nullable=False)  # inverter, pyranometer, transformer, combiner_box
    capacity_kw = Column(Float, default=5000.0)
    model = Column(String(128), default="SMA-Central-5000")
    status = Column(String(32), default="operational")  # operational, degraded, offline, maintenance
    created_at = Column(DateTime, default=datetime.utcnow)

    plant = relationship("Plant", back_populates="assets")
