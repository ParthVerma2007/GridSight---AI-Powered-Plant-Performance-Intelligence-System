from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.plant import Plant, Asset
from app.models.equipment import EquipmentTelemetry
from app.models.maintenance import MaintenanceRecord
from app.models.external_events import ExternalEvent
from app.models.investigation import Investigation
from app.models.work_order import WorkOrder
from app.schemas.analytics import KPISummary
from app.schemas.attribution import VarianceAttributionReport
from app.schemas.ai import CompactContextPackage
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.attribution.engine import VarianceAttributionEngine

class ContextPackageBuilder:
    def __init__(self, db: Session, plant_id: str = "helios-50"):
        self.db = db
        self.plant_id = plant_id
        self.analytics = DeterministicAnalyticsEngine(db, plant_id)
        self.attribution_engine = VarianceAttributionEngine(db, plant_id)

    def build_compact_context(
        self,
        role: str,
        start_time: datetime,
        end_time: datetime,
        user_question: Optional[str] = None,
        forecast_version: str = "day_ahead_v1"
    ) -> CompactContextPackage:
        """
        Builds a role-specific compact context package containing only relevant,
        verified metrics, events, and evidence references.
        Avoids sending raw CSV dumps or voluminous raw telemetry.
        """
        role_upper = role.upper()
        kpi = self.analytics.compute_kpis(start_time, end_time, forecast_version)
        attribution = self.attribution_engine.attribute_variance(start_time, end_time, forecast_version)
        fin_params = self.analytics.get_financial_parameters(start_time.date())

        # Base verified metrics
        verified_metrics = {
            "expected_mwh": kpi.expected_generation_mwh,
            "actual_mwh": kpi.actual_generation_mwh,
            "variance_mwh": kpi.variance_mwh,
            "variance_pct": kpi.variance_pct,
            "capacity_factor_pct": kpi.capacity_factor_pct,
            "availability_pct": kpi.availability_pct,
            "downtime_hours": kpi.downtime_hours,
            "realized_revenue_usd": kpi.realized_revenue_usd,
            "lost_revenue_usd": kpi.lost_revenue_usd,
            "ppa_tariff_usd_per_mwh": fin_params["ppa_tariff"],
            "reconciliation_valid": attribution.reconciliation_valid
        }

        # Compact attributed causes
        causes_summary = []
        for c in attribution.causes:
            causes_summary.append({
                "cause_id": c.cause_id,
                "category": c.category,
                "title": c.title,
                "asset_id": c.asset_id,
                "loss_mwh": c.attributed_loss_mwh,
                "loss_usd": c.attributed_financial_loss_usd,
                "share_pct": c.share_of_variance_pct,
                "predictability": c.predictability,
                "controllability": c.controllability,
                "recurrence": c.recurrence,
                "severity": c.severity,
                "evidence_sources": [f"{e.source_type}:{e.metric_name}={e.metric_value}" for e in c.evidence]
            })

        # Related events (curtailment, weather anomalies)
        events_summary = []
        events = self.db.query(ExternalEvent).filter(
            ExternalEvent.plant_id == self.plant_id,
            ExternalEvent.timestamp_start <= end_time,
            ExternalEvent.timestamp_end >= start_time
        ).all()
        for ev in events:
            events_summary.append({
                "event_type": ev.event_type,
                "start": ev.timestamp_start.isoformat(),
                "curtailed_mw": ev.curtailed_capacity_mw,
                "directive": ev.iso_directive_code,
                "description": ev.impact_description
            })

        # Role-tailored filtering
        alarms_summary = []
        if role_upper == "TECHNICIAN":
            # For technician: include active alarms, sensor anomalies, and work orders
            alarms = self.db.query(EquipmentTelemetry).filter(
                EquipmentTelemetry.timestamp >= start_time,
                EquipmentTelemetry.timestamp <= end_time,
                EquipmentTelemetry.alarm_code != None
            ).order_by(EquipmentTelemetry.timestamp.desc()).limit(15).all()

            for a in alarms:
                alarms_summary.append({
                    "asset_id": a.asset_id,
                    "timestamp": a.timestamp.isoformat(),
                    "temp_c": a.inverter_temp_c,
                    "alarm_code": a.alarm_code,
                    "description": a.alarm_description,
                    "state": a.operating_state
                })
        elif role_upper == "OPERATIONS":
            # For operations: high level alarm counts and recurring items
            fault_counts = self.db.query(
                EquipmentTelemetry.asset_id,
                func.count(EquipmentTelemetry.id).label("alarm_count")
            ).filter(
                EquipmentTelemetry.timestamp >= start_time,
                EquipmentTelemetry.timestamp <= end_time,
                EquipmentTelemetry.alarm_code != None
            ).group_by(EquipmentTelemetry.asset_id).all()

            for fc in fault_counts:
                alarms_summary.append({
                    "asset_id": fc.asset_id,
                    "alarm_count": fc.alarm_count,
                    "summary": f"{fc.alarm_count} fault instances logged during period"
                })
        else:
            # CEO/CFO: NO raw telemetry; only financial impact
            alarms_summary = []

        return CompactContextPackage(
            user_role=role_upper,
            plant_id=self.plant_id,
            plant_name="Helios-50 Solar Farm",
            period_start=start_time.isoformat(),
            period_end=end_time.isoformat(),
            verified_metrics=verified_metrics,
            attributed_causes=causes_summary,
            related_events=events_summary,
            equipment_alarms=alarms_summary,
            financial_parameters={
                "ppa_tariff": fin_params["ppa_tariff"],
                "om_hourly_cost": fin_params["om_hourly_cost"],
                "budgeted_revenue": fin_params["budgeted_monthly_revenue"]
            },
            user_question=user_question
        )
