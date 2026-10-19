from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.attribution.engine import VarianceAttributionEngine
from app.context.builder import ContextPackageBuilder
from app.ai.service import ai_service
from app.schemas.dashboards import ExecutiveDashboardResponse, OperationsDashboardResponse, TechnicianDashboardResponse
from app.auth.rbac import get_current_role, require_role, UserRole
from app.api.v1.analytics import get_default_time_range
from app.models.plant import Asset
from app.models.equipment import EquipmentTelemetry
from app.models.maintenance import MaintenanceRecord
from app.models.external_events import ExternalEvent
from app.models.workforce import WorkforceRecord
from app.models.investigation import Investigation
from app.models.work_order import WorkOrder

router = APIRouter(prefix="/dashboards", tags=["Role-Specific Dashboards"])

@router.get("/executive", response_model=ExecutiveDashboardResponse)
async def get_executive_dashboard(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.CEO, UserRole.CFO, UserRole.OPERATIONS, UserRole.ADMIN]))
):
    """
    CEO/CFO Executive Dashboard.
    Tailored for strategic financial decisions, budget variance, recurring revenue drag,
    major risks, and approval requests. Excludes raw telemetry by default.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    analytics = DeterministicAnalyticsEngine(db, plant_id)
    attribution_engine = VarianceAttributionEngine(db, plant_id)
    builder = ContextPackageBuilder(db, plant_id)

    # 1. Consistent underlying KPIs
    kpi = analytics.compute_kpis(start_time, end_time, forecast_version)
    attribution = attribution_engine.attribute_variance(start_time, end_time, forecast_version)
    fin_params = analytics.get_financial_parameters(start_time.date())

    # 2. Executive specific rollups
    recurring_causes = [c for c in attribution.causes if c.recurrence == "recurring"]
    recurring_loss_mwh = sum(c.attributed_loss_mwh for c in recurring_causes)
    recurring_loss_usd = sum(c.attributed_financial_loss_usd for c in recurring_causes)

    revenue_vs_budget = {
        "budgeted_revenue_usd": kpi.budgeted_revenue_usd,
        "realized_revenue_usd": kpi.realized_revenue_usd,
        "revenue_gap_usd": round(kpi.realized_revenue_usd - kpi.budgeted_revenue_usd, 2),
        "target_achievement_pct": round(kpi.realized_revenue_usd / max(1.0, kpi.budgeted_revenue_usd) * 100.0, 1),
        "total_lost_revenue_usd": kpi.lost_revenue_usd,
        "opex_incurred_usd": kpi.opex_cost_usd,
        "net_operating_margin_usd": round(kpi.realized_revenue_usd - kpi.opex_cost_usd, 2)
    }

    recurring_losses_summary = {
        "recurring_loss_mwh": round(recurring_loss_mwh, 2),
        "recurring_loss_usd": round(recurring_loss_usd, 2),
        "primary_asset_impacted": "INV-04 (Inverter Central Unit 04)",
        "annualized_risk_usd": round(recurring_loss_usd * 12.0, 2),
        "recurrence_driver": "Cooling blower degradation under high ambient temperature"
    }

    strategic_risks = [
        f"Contractual PPA availability threshold at 95.0% (Current Plant Availability: {kpi.availability_pct:.1f}%).",
        f"Unmitigated recurring thermal fault on Inverter #04 projects annualized revenue loss of ${recurring_loss_usd * 12:,.2f}.",
        f"Grid congestion in regional transmission corridor is causing uncompensated curtailment risk during high-irradiance hours."
    ]

    decisions_requiring_approval = [
        {
            "id": "DEC-2026-001",
            "title": "Capital Expenditure: Inverter #04 Cooling Module Replacement",
            "estimated_cost_usd": 4200.00,
            "projected_payback_days": 18.5,
            "status": "pending_executive_signoff",
            "urgency": "high"
        },
        {
            "id": "DEC-2026-002",
            "title": "CAISO Curtailment PPA Dispute Filing (Clause 14.2)",
            "estimated_recovery_usd": round(kpi.curtailment_mwh * fin_params["curtailment_comp"], 2),
            "status": "under_legal_review",
            "urgency": "medium"
        }
    ]

    # 3. Compact context and AI explanation
    ctx = builder.build_compact_context("CEO", start_time, end_time, forecast_version=forecast_version)
    ai_insights = await ai_service.generate_explanation(ctx)

    high_level_causes = [{
        "title": c.title,
        "loss_mwh": c.attributed_loss_mwh,
        "loss_usd": c.attributed_financial_loss_usd,
        "share_pct": c.share_of_variance_pct,
        "category": c.category
    } for c in attribution.causes]

    return ExecutiveDashboardResponse(
        role="CEO",
        plant_id=plant_id,
        period_start=start_time,
        period_end=end_time,
        kpi=kpi,
        revenue_vs_budget=revenue_vs_budget,
        recurring_losses_summary=recurring_losses_summary,
        strategic_risks=strategic_risks,
        decisions_requiring_approval=decisions_requiring_approval,
        ai_insights=ai_insights,
        high_level_causes=high_level_causes
    )

@router.get("/operations", response_model=OperationsDashboardResponse)
async def get_operations_dashboard(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.OPERATIONS, UserRole.ADMIN, UserRole.CEO]))
):
    """
    Operations Management Dashboard.
    Tailored for variance bridge, equipment availability, root cause attribution,
    investigation tracking, action ownership, and shift management.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    analytics = DeterministicAnalyticsEngine(db, plant_id)
    attribution_engine = VarianceAttributionEngine(db, plant_id)
    builder = ContextPackageBuilder(db, plant_id)

    kpi = analytics.compute_kpis(start_time, end_time, forecast_version)
    attribution = attribution_engine.attribute_variance(start_time, end_time, forecast_version)
    time_series = analytics.get_time_series(start_time, end_time, forecast_version)
    daily_perf = analytics.get_daily_performance(start_time, end_time, forecast_version)

    # Active investigations
    investigations = db.query(Investigation).filter(
        Investigation.plant_id == plant_id
    ).order_by(Investigation.updated_at.desc()).all()

    inv_list = [{
        "id": inv.id,
        "title": inv.title,
        "cause_id": inv.cause_id,
        "category": inv.cause_category,
        "owner": inv.owner,
        "status": inv.status,
        "priority": inv.priority,
        "controllability": inv.controllability,
        "recurrence_flag": inv.recurrence_flag,
        "deadline": inv.deadline.isoformat() if inv.deadline else None,
        "action_plan": inv.action_plan
    } for inv in investigations]

    # Grid and weather events
    events = db.query(ExternalEvent).filter(
        ExternalEvent.plant_id == plant_id,
        ExternalEvent.timestamp_start <= end_time,
        ExternalEvent.timestamp_end >= start_time
    ).all()

    event_list = [{
        "id": ev.id,
        "event_type": ev.event_type,
        "curtailed_capacity_mw": ev.curtailed_capacity_mw,
        "directive_code": ev.iso_directive_code,
        "start": ev.timestamp_start.isoformat(),
        "end": ev.timestamp_end.isoformat(),
        "notes": ev.impact_description
    } for ev in events]

    # Workforce status
    workforce = db.query(WorkforceRecord).filter(
        WorkforceRecord.plant_id == plant_id,
        WorkforceRecord.date >= start_time.date(),
        WorkforceRecord.date <= end_time.date()
    ).all()

    workforce_list = [{
        "date": w.date.isoformat(),
        "shift": w.shift,
        "technicians_on_site": w.technicians_on_site,
        "lead_technician": w.lead_technician,
        "hours_logged": w.hours_logged,
        "certifications": w.skill_certifications
    } for w in workforce]

    ctx = builder.build_compact_context("OPERATIONS", start_time, end_time, forecast_version=forecast_version)
    ai_insights = await ai_service.generate_explanation(ctx)

    return OperationsDashboardResponse(
        role="OPERATIONS",
        plant_id=plant_id,
        period_start=start_time,
        period_end=end_time,
        kpi=kpi,
        time_series=time_series,
        daily_performance=daily_perf,
        attribution=attribution,
        active_investigations=inv_list,
        grid_and_weather_events=event_list,
        workforce_status=workforce_list,
        ai_insights=ai_insights
    )

@router.get("/technician", response_model=TechnicianDashboardResponse)
async def get_technician_dashboard(
    plant_id: str = "helios-50",
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    forecast_version: str = "day_ahead_v1",
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.TECHNICIAN, UserRole.OPERATIONS, UserRole.ADMIN]))
):
    """
    Field Technician Dashboard.
    Tailored for asset health, sensor trends, active alarms, work orders,
    approved procedures, and AI-assisted troubleshooting checklists.
    STRICT NOTICE: Read-only intelligence. Autonomous machine control and
    bypassing safety interlocks are strictly prevented.
    """
    if not start_time or not end_time:
        start_time, end_time = get_default_time_range(db, plant_id)

    analytics = DeterministicAnalyticsEngine(db, plant_id)
    builder = ContextPackageBuilder(db, plant_id)
    kpi = analytics.compute_kpis(start_time, end_time, forecast_version)

    # Asset statuses
    assets = db.query(Asset).filter(Asset.plant_id == plant_id).all()
    asset_list = []
    sensor_trends = {}

    for a in assets:
        latest = db.query(EquipmentTelemetry).filter(
            EquipmentTelemetry.asset_id == a.id
        ).order_by(EquipmentTelemetry.timestamp.desc()).first()

        status = a.status
        if latest and latest.operating_state in ["fault_trip", "offline"]:
            status = "fault_trip"
        elif latest and latest.inverter_temp_c and latest.inverter_temp_c > 65.0:
            status = "degraded"

        asset_list.append({
            "asset_id": a.id,
            "name": a.name,
            "type": a.asset_type,
            "capacity_kw": a.capacity_kw,
            "model": a.model,
            "status": status,
            "latest_temp_c": latest.inverter_temp_c if latest else None,
            "latest_ac_kw": latest.ac_power_kw if latest else None,
            "latest_alarm": latest.alarm_code if latest else None
        })

    # Sensor trends for key assets (e.g. INV-04 vs peer INV-01)
    for target_inv in ["INV-04", "INV-01", "INV-02"]:
        telem_pts = db.query(EquipmentTelemetry).filter(
            EquipmentTelemetry.asset_id == target_inv,
            EquipmentTelemetry.timestamp >= start_time,
            EquipmentTelemetry.timestamp <= end_time
        ).order_by(EquipmentTelemetry.timestamp.asc()).all()

        sensor_trends[target_inv] = [{
            "timestamp": t.timestamp.isoformat(),
            "temp_c": t.inverter_temp_c,
            "ac_power_kw": t.ac_power_kw,
            "dc_voltage_v": t.dc_voltage_v,
            "operating_state": t.operating_state,
            "alarm": t.alarm_code
        } for t in telem_pts]

    # Active alarms
    alarms = db.query(EquipmentTelemetry).filter(
        EquipmentTelemetry.timestamp >= start_time,
        EquipmentTelemetry.timestamp <= end_time,
        EquipmentTelemetry.alarm_code != None
    ).order_by(EquipmentTelemetry.timestamp.desc()).limit(20).all()

    active_alarms = [{
        "id": al.id,
        "asset_id": al.asset_id,
        "timestamp": al.timestamp.isoformat(),
        "alarm_code": al.alarm_code,
        "description": al.alarm_description,
        "inverter_temp_c": al.inverter_temp_c,
        "operating_state": al.operating_state
    } for al in alarms]

    # Work orders
    work_orders = db.query(WorkOrder).filter(
        WorkOrder.plant_id == plant_id
    ).order_by(WorkOrder.created_at.desc()).all()

    wo_list = [{
        "id": wo.id,
        "work_order_number": wo.work_order_number,
        "asset_id": wo.asset_id,
        "title": wo.title,
        "description": wo.description,
        "priority": wo.priority,
        "status": wo.status,
        "assigned_technician": wo.assigned_technician,
        "estimated_hours": wo.estimated_hours,
        "procedure_code": wo.procedure_code,
        "safety_interlock_verified": wo.safety_interlock_verified,
        "loto_applied": wo.loto_applied
    } for wo in work_orders]

    # Maintenance history
    maint_recs = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.plant_id == plant_id
    ).order_by(MaintenanceRecord.scheduled_start.desc()).limit(10).all()

    maint_list = [{
        "work_order_id": m.work_order_id,
        "asset_id": m.asset_id,
        "type": m.maintenance_type,
        "scheduled_start": m.scheduled_start.isoformat(),
        "downtime_hours": m.downtime_hours,
        "technician": m.technician_in_charge,
        "procedure": m.procedure_code,
        "status": m.status
    } for m in maint_recs]

    ctx = builder.build_compact_context("TECHNICIAN", start_time, end_time, forecast_version=forecast_version)
    ai_troubleshooting = await ai_service.generate_explanation(ctx)

    safety_notice = (
        "SAFETY MANDATE: Strictly read-only advisory interface. "
        "Autonomous equipment control and bypassing electrical safety interlocks or Lockout/Tagout (LOTO) "
        "are strictly prohibited by system architecture and NFPA 70E / OSHA standards."
    )

    return TechnicianDashboardResponse(
        role="TECHNICIAN",
        plant_id=plant_id,
        period_start=start_time,
        period_end=end_time,
        kpi=kpi,
        asset_status_list=asset_list,
        active_alarms=active_alarms,
        sensor_trends=sensor_trends,
        work_orders=wo_list,
        maintenance_history=maint_list,
        ai_troubleshooting=ai_troubleshooting,
        safety_interlock_notice=safety_notice
    )
