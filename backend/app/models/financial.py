from sqlalchemy import Column, String, Float, DateTime, Integer, Date, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base

class FinancialAssumption(Base):
    __tablename__ = "financial_assumptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String(64), ForeignKey("plants.id"), nullable=False, index=True)
    effective_date = Column(Date, nullable=False, index=True)
    ppa_tariff_usd_per_mwh = Column(Float, nullable=False, default=48.50)
    om_hourly_cost_usd = Column(Float, nullable=False, default=125.00)
    curtailment_compensation_usd_per_mwh = Column(Float, nullable=False, default=40.00)
    budgeted_monthly_generation_mwh = Column(Float, nullable=False, default=8500.0)
    budgeted_monthly_revenue_usd = Column(Float, nullable=False, default=412250.0)
    budgeted_monthly_opex_usd = Column(Float, nullable=False, default=38000.0)
    source_file = Column(String(256), nullable=False)
    source_row_index = Column(Integer, nullable=False)
    ingestion_batch_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plant_id", "effective_date", name="uq_financial_plant_date"),
    )
