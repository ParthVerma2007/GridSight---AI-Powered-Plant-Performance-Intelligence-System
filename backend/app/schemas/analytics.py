from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    expected_mw: float
    actual_mw: float
    variance_mw: float
    ghi_actual: Optional[float] = None
    ghi_expected: Optional[float] = None

class KPISummary(BaseModel):
    plant_id: str
    period_start: datetime
    period_end: datetime
    expected_generation_mwh: float
    actual_generation_mwh: float
    variance_mwh: float
    variance_pct: float
    capacity_factor_pct: float
    availability_pct: float
    downtime_hours: float
    curtailment_mwh: float
    financial_impact_usd: float
    realized_revenue_usd: float
    lost_revenue_usd: float
    budgeted_revenue_usd: float
    opex_cost_usd: float

class DailyPerformanceItem(BaseModel):
    date: str
    expected_mwh: float
    actual_mwh: float
    variance_mwh: float
    availability_pct: float
    lost_revenue_usd: float
    dominant_cause: Optional[str] = None
