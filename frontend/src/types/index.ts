export type UserRole = 'CEO' | 'OPERATIONS' | 'TECHNICIAN';

export interface KPISummary {
  plant_id: string;
  period_start: string;
  period_end: string;
  expected_generation_mwh: number;
  actual_generation_mwh: number;
  variance_mwh: number;
  variance_pct: number;
  capacity_factor_pct: number;
  availability_pct: number;
  downtime_hours: number;
  curtailment_mwh: number;
  financial_impact_usd: number;
  realized_revenue_usd: number;
  lost_revenue_usd: number;
  budgeted_revenue_usd: number;
  opex_cost_usd: number;
}

export interface TimeSeriesPoint {
  timestamp: string;
  expected_mw: number;
  actual_mw: number;
  variance_mw: number;
  ghi_actual?: number | null;
  ghi_expected?: number | null;
}

export interface DailyPerformanceItem {
  date: string;
  expected_mwh: number;
  actual_mwh: number;
  variance_mwh: number;
  availability_pct: number;
  lost_revenue_usd: number;
  dominant_cause?: string;
}

export interface EvidenceReference {
  source_type: string;
  source_id: string;
  record_timestamp?: string;
  metric_name: string;
  metric_value: any;
  baseline_value?: any;
  description: string;
}

export interface AttributedCause {
  cause_id: string;
  category: string;
  title: string;
  description: string;
  asset_id?: string | null;
  attributed_loss_mwh: number;
  attributed_financial_loss_usd: number;
  share_of_variance_pct: number;
  calculation_method: string;
  confidence_basis: string;
  confidence_score: number;
  attribution_status: string;
  predictability: string;
  controllability: string;
  recurrence: string;
  severity: string;
  evidence: EvidenceReference[];
}

export interface WaterfallStep {
  name: string;
  value: number;
  delta?: number;
  category?: string;
  type: 'baseline' | 'cause' | 'actual';
}

export interface VarianceAttributionReport {
  plant_id: string;
  period_start: string;
  period_end: string;
  forecast_version: string;
  expected_mwh: number;
  actual_mwh: number;
  total_variance_mwh: number;
  total_attributed_loss_mwh: number;
  unexplained_residual_mwh: number;
  reconciliation_discrepancy_mwh: number;
  reconciliation_valid: boolean;
  causes: AttributedCause[];
  waterfall_steps: WaterfallStep[];
}

export interface AIActionItem {
  priority: string;
  action: string;
  owner_role: string;
  rationale: string;
  safety_precaution?: string | null;
}

export interface AIExplanationResponse {
  role: string;
  summary: string;
  verified_facts: string[];
  supported_explanations: string[];
  hypotheses: string[];
  unknowns: string[];
  strategic_or_operational_risks: string[];
  recommended_actions: AIActionItem[];
  citations_and_evidence: string[];
  provider_used: string;
  validation_status: string;
}

export interface ExecutiveDashboardResponse {
  role: string;
  plant_id: string;
  period_start: string;
  period_end: string;
  kpi: KPISummary;
  revenue_vs_budget: {
    budgeted_revenue_usd: number;
    realized_revenue_usd: number;
    revenue_gap_usd: number;
    target_achievement_pct: number;
    total_lost_revenue_usd: number;
    opex_incurred_usd: number;
    net_operating_margin_usd: number;
  };
  recurring_losses_summary: {
    recurring_loss_mwh: number;
    recurring_loss_usd: number;
    primary_asset_impacted: string;
    annualized_risk_usd: number;
    recurrence_driver: string;
  };
  strategic_risks: string[];
  decisions_requiring_approval: Array<{
    id: string;
    title: string;
    estimated_cost_usd?: number;
    estimated_recovery_usd?: number;
    projected_payback_days?: number;
    status: string;
    urgency: string;
  }>;
  ai_insights: AIExplanationResponse;
  high_level_causes: Array<{
    title: string;
    loss_mwh: number;
    loss_usd: number;
    share_pct: number;
    category: string;
  }>;
}

export interface OperationsDashboardResponse {
  role: string;
  plant_id: string;
  period_start: string;
  period_end: string;
  kpi: KPISummary;
  time_series: TimeSeriesPoint[];
  daily_performance: DailyPerformanceItem[];
  attribution: VarianceAttributionReport;
  active_investigations: any[];
  grid_and_weather_events: any[];
  workforce_status: any[];
  ai_insights: AIExplanationResponse;
}

export interface TechnicianDashboardResponse {
  role: string;
  plant_id: string;
  period_start: string;
  period_end: string;
  kpi: KPISummary;
  asset_status_list: Array<{
    asset_id: string;
    name: string;
    type: string;
    capacity_kw: number;
    model: string;
    status: string;
    latest_temp_c?: number;
    latest_ac_kw?: number;
    latest_alarm?: string;
  }>;
  active_alarms: Array<{
    id: number;
    asset_id: string;
    timestamp: string;
    alarm_code: string;
    description: string;
    inverter_temp_c?: number;
    operating_state: string;
  }>;
  sensor_trends: Record<string, Array<{
    timestamp: string;
    temp_c?: number;
    ac_power_kw?: number;
    dc_voltage_v?: number;
    operating_state: string;
    alarm?: string;
  }>>;
  work_orders: Array<{
    id: number;
    work_order_number: string;
    asset_id: string;
    title: string;
    description: string;
    priority: string;
    status: string;
    assigned_technician: string;
    estimated_hours: number;
    procedure_code: string;
    safety_interlock_verified: boolean;
    loto_applied: boolean;
  }>;
  maintenance_history: any[];
  ai_troubleshooting: AIExplanationResponse;
  safety_interlock_notice: string;
}

export interface IngestionBatch {
  batch_id: string;
  source_file: string;
  file_type: string;
  total_records: number;
  valid_records: number;
  quarantined_records: number;
  success_rate_pct: number;
  status: string;
  summary: string;
  created_at: string;
}

export interface QuarantineItem {
  id: number;
  source_file: string;
  row_index: number;
  raw_content: string;
  error_type: string;
  error_detail: string;
  quarantined_at: string;
}
