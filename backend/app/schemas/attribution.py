from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class EvidenceReference(BaseModel):
    source_type: str  # telemetry, alarm, weather, iso_order, maintenance_log
    source_id: str
    record_timestamp: Optional[datetime] = None
    metric_name: str
    metric_value: Any
    baseline_value: Optional[Any] = None
    description: str

class AttributedCause(BaseModel):
    cause_id: str
    category: str  # equipment_fault, weather, grid_curtailment, maintenance, operational_constraint, unexplained_residual
    title: str
    description: str
    asset_id: Optional[str] = None
    attributed_loss_mwh: float
    attributed_financial_loss_usd: float
    share_of_variance_pct: float
    calculation_method: str  # physical_model, baseline_difference, meter_delta, residual
    confidence_basis: str    # high_sensor_evidence, direct_curtailment_order, pyranometer_delta, mathematical_residual
    confidence_score: float  # 0.0 to 1.0
    attribution_status: str  # confirmed, preliminary, residual
    predictability: str      # planned, unplanned, force_majeure
    controllability: str     # controllable, semi_controllable, uncontrollable
    recurrence: str          # one_off, recurring, intermittent
    severity: str            # critical, high, medium, low
    evidence: List[EvidenceReference] = []

class VarianceAttributionReport(BaseModel):
    plant_id: str
    period_start: datetime
    period_end: datetime
    forecast_version: str
    expected_mwh: float
    actual_mwh: float
    total_variance_mwh: float
    total_attributed_loss_mwh: float
    unexplained_residual_mwh: float
    reconciliation_discrepancy_mwh: float  # Must be 0.000 or within float epsilon
    reconciliation_valid: bool
    causes: List[AttributedCause]
    waterfall_steps: List[Dict[str, Any]]
