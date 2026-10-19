from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.schemas.analytics import KPISummary, TimeSeriesPoint, DailyPerformanceItem
from app.schemas.attribution import VarianceAttributionReport, AttributedCause
from app.schemas.ai import AIExplanationResponse

class ExecutiveDashboardResponse(BaseModel):
    role: str = "CEO"
    plant_id: str
    period_start: datetime
    period_end: datetime
    kpi: KPISummary
    revenue_vs_budget: Dict[str, Any]
    recurring_losses_summary: Dict[str, Any]
    strategic_risks: List[str]
    decisions_requiring_approval: List[Dict[str, Any]]
    ai_insights: AIExplanationResponse
    high_level_causes: List[Dict[str, Any]]

class OperationsDashboardResponse(BaseModel):
    role: str = "OPERATIONS"
    plant_id: str
    period_start: datetime
    period_end: datetime
    kpi: KPISummary
    time_series: List[TimeSeriesPoint]
    daily_performance: List[DailyPerformanceItem]
    attribution: VarianceAttributionReport
    active_investigations: List[Dict[str, Any]]
    grid_and_weather_events: List[Dict[str, Any]]
    workforce_status: List[Dict[str, Any]]
    ai_insights: AIExplanationResponse

class TechnicianDashboardResponse(BaseModel):
    role: str = "TECHNICIAN"
    plant_id: str
    period_start: datetime
    period_end: datetime
    kpi: KPISummary
    asset_status_list: List[Dict[str, Any]]
    active_alarms: List[Dict[str, Any]]
    sensor_trends: Dict[str, List[Dict[str, Any]]]
    work_orders: List[Dict[str, Any]]
    maintenance_history: List[Dict[str, Any]]
    ai_troubleshooting: AIExplanationResponse
    safety_interlock_notice: str
