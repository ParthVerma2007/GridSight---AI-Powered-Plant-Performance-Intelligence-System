from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.plant import Plant, Asset
from app.models.generation import GenerationRecord
from app.models.forecast import ForecastRecord
from app.models.equipment import EquipmentTelemetry
from app.models.weather import WeatherRecord
from app.models.maintenance import MaintenanceRecord
from app.models.external_events import ExternalEvent
from app.models.financial import FinancialAssumption
from app.schemas.attribution import AttributedCause, EvidenceReference, VarianceAttributionReport
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.config import settings

class VarianceAttributionEngine:
    def __init__(self, db: Session, plant_id: str = "helios-50"):
        self.db = db
        self.plant_id = plant_id
        self.analytics = DeterministicAnalyticsEngine(db, plant_id)

    def attribute_variance(
        self,
        start_time: datetime,
        end_time: datetime,
        forecast_version: str = "day_ahead_v1"
    ) -> VarianceAttributionReport:
        """
        Executes deterministic cause-based variance attribution.
        Prevents double-counting, reconciles against total variance,
        preserves unexplained residuals, and outputs verifiable evidence references.
        """
        kpi = self.analytics.compute_kpis(start_time, end_time, forecast_version)
        fin = self.analytics.get_financial_parameters(start_time.date())
        tariff = fin["ppa_tariff"]

        expected_mwh = kpi.expected_generation_mwh
        actual_mwh = kpi.actual_generation_mwh
        total_variance_mwh = actual_mwh - expected_mwh
        
        # When variance is negative, we attribute the lost MWh
        # When variance is positive, plant generated surplus energy
        is_loss = total_variance_mwh < -0.01
        loss_mwh_to_attribute = abs(min(0.0, total_variance_mwh))

        raw_causes: List[AttributedCause] = []

        if is_loss and loss_mwh_to_attribute > 0:
            # 1. Equipment Faults Attribution (e.g. Inverter 04 Overheating Trip)
            equip_causes = self._attribute_equipment_faults(start_time, end_time, tariff)
            raw_causes.extend(equip_causes)

            # 2. Grid Curtailment Attribution (CAISO / Grid directives)
            curt_causes = self._attribute_grid_curtailment(start_time, end_time, tariff)
            raw_causes.extend(curt_causes)

            # 3. Weather Variance Attribution (Low Irradiance / Cloud Cover)
            weather_causes = self._attribute_weather_variance(start_time, end_time, tariff, expected_mwh)
            raw_causes.extend(weather_causes)

            # 4. Planned Maintenance Attribution
            maint_causes = self._attribute_maintenance(start_time, end_time, tariff)
            raw_causes.extend(maint_causes)

        # Reconcile and prevent double-counting
        total_raw_attributed = sum(c.attributed_loss_mwh for c in raw_causes)
        final_causes: List[AttributedCause] = []

        if total_raw_attributed > loss_mwh_to_attribute and total_raw_attributed > 0:
            # Scale proportionally to prevent double-counting
            scale_factor = loss_mwh_to_attribute / total_raw_attributed
            for c in raw_causes:
                scaled_loss = round(c.attributed_loss_mwh * scale_factor, 2)
                scaled_usd = round(scaled_loss * tariff, 2)
                share_pct = round((scaled_loss / loss_mwh_to_attribute * 100.0), 1) if loss_mwh_to_attribute > 0 else 0.0
                c.attributed_loss_mwh = scaled_loss
                c.attributed_financial_loss_usd = scaled_usd
                c.share_of_variance_pct = share_pct
                final_causes.append(c)
            unexplained_residual_mwh = 0.0
        else:
            # Attributed fits within total variance; remainder is preserved as Unexplained Residual
            for c in raw_causes:
                share_pct = round((c.attributed_loss_mwh / loss_mwh_to_attribute * 100.0), 1) if loss_mwh_to_attribute > 0 else 0.0
                c.share_of_variance_pct = share_pct
                final_causes.append(c)

            unexplained_residual_mwh = round(max(0.0, loss_mwh_to_attribute - total_raw_attributed), 2)
            if unexplained_residual_mwh > 0.05:
                residual_usd = round(unexplained_residual_mwh * tariff, 2)
                share_pct = round((unexplained_residual_mwh / loss_mwh_to_attribute * 100.0), 1) if loss_mwh_to_attribute > 0 else 0.0
                final_causes.append(AttributedCause(
                    cause_id="CAUSE-RESIDUAL-UNEXPLAINED",
                    category="unexplained_residual",
                    title="Unexplained Discrepancy & Sensor Margin",
                    description=f"Residual shortfall of {unexplained_residual_mwh} MWh not directly attributable to telemetry alarms, weather deltas, or grid curtailment records.",
                    asset_id=None,
                    attributed_loss_mwh=unexplained_residual_mwh,
                    attributed_financial_loss_usd=residual_usd,
                    share_of_variance_pct=share_pct,
                    calculation_method="residual",
                    confidence_basis="mathematical_residual",
                    confidence_score=0.40,
                    attribution_status="residual",
                    predictability="unplanned",
                    controllability="controllable",
                    recurrence="intermittent",
                    severity="low",
                    evidence=[
                        EvidenceReference(
                            source_type="analytics_engine",
                            source_id="reconciliation_pipeline",
                            record_timestamp=start_time,
                            metric_name="unexplained_residual",
                            metric_value=f"{unexplained_residual_mwh} MWh",
                            baseline_value="0.0 MWh",
                            description="Mathematical delta between total verified variance and sum of evidence-supported causes."
                        )
                    ]
                ))

        # Recompute totals and verify mathematical reconciliation
        total_attributed_mwh = sum(c.attributed_loss_mwh for c in final_causes if c.category != "unexplained_residual")
        total_reconciled = total_attributed_mwh + unexplained_residual_mwh
        discrepancy = round(abs(loss_mwh_to_attribute - total_reconciled), 4)
        reconciliation_valid = discrepancy <= 0.05

        # Build waterfall steps for UI chart visualization
        waterfall_steps = self._build_waterfall_steps(expected_mwh, actual_mwh, final_causes)

        return VarianceAttributionReport(
            plant_id=self.plant_id,
            period_start=start_time,
            period_end=end_time,
            forecast_version=forecast_version,
            expected_mwh=expected_mwh,
            actual_mwh=actual_mwh,
            total_variance_mwh=round(total_variance_mwh, 2),
            total_attributed_loss_mwh=round(total_attributed_mwh, 2),
            unexplained_residual_mwh=round(unexplained_residual_mwh, 2),
            reconciliation_discrepancy_mwh=discrepancy,
            reconciliation_valid=reconciliation_valid,
            causes=final_causes,
            waterfall_steps=waterfall_steps
        )

    def _attribute_equipment_faults(self, start_time: datetime, end_time: datetime, tariff: float) -> List[AttributedCause]:
        """
        Attributes losses to specific equipment faults by comparing faulted asset output
        against healthy peer asset benchmarks at each hour.
        """
        causes = []

        # Find assets with alarms or fault states
        fault_telemetry = self.db.query(EquipmentTelemetry).filter(
            EquipmentTelemetry.timestamp >= start_time,
            EquipmentTelemetry.timestamp <= end_time,
            (EquipmentTelemetry.operating_state.in_(["fault_trip", "offline"])) |
            ((EquipmentTelemetry.alarm_code != None) & (EquipmentTelemetry.alarm_code != ""))
        ).all()

        if not fault_telemetry:
            return causes

        # Group by asset_id
        asset_faults: Dict[str, List[EquipmentTelemetry]] = {}
        for t in fault_telemetry:
            asset_faults.setdefault(t.asset_id, []).append(t)

        for asset_id, records in asset_faults.items():
            total_loss_mwh = 0.0
            evidence_list: List[EvidenceReference] = []
            alarm_codes = set()
            max_temp = 0.0

            for rec in records:
                if rec.alarm_code:
                    alarm_codes.add(rec.alarm_code)
                if rec.inverter_temp_c and rec.inverter_temp_c > max_temp:
                    max_temp = rec.inverter_temp_c

                # Calculate peer benchmark for this timestamp
                peer_telem = self.db.query(
                    func.avg(EquipmentTelemetry.ac_power_kw).label("avg_kw")
                ).filter(
                    EquipmentTelemetry.timestamp == rec.timestamp,
                    EquipmentTelemetry.asset_id != asset_id,
                    EquipmentTelemetry.operating_state == "running"
                ).first()

                peer_benchmark_kw = peer_telem.avg_kw if peer_telem and peer_telem.avg_kw else 4200.0
                actual_kw = rec.ac_power_kw or 0.0
                lost_kw = max(0.0, peer_benchmark_kw - actual_kw)
                lost_mwh = lost_kw / 1000.0  # 1 hour interval
                total_loss_mwh += lost_mwh

                if len(evidence_list) < 3 and rec.alarm_code:
                    evidence_list.append(EvidenceReference(
                        source_type="telemetry",
                        source_id=f"TELEMETRY-{rec.id}",
                        record_timestamp=rec.timestamp,
                        metric_name="inverter_temp_c",
                        metric_value=f"{rec.inverter_temp_c}°C (Alarm: {rec.alarm_code})",
                        baseline_value="< 55.0°C Safe Operating Threshold",
                        description=f"{rec.alarm_description or 'Inverter tripped on overtemperature during peak irradiance'}"
                    ))

            total_loss_mwh = round(total_loss_mwh, 2)
            if total_loss_mwh > 0.1:
                financial_loss = round(total_loss_mwh * tariff, 2)
                is_recurring = len(records) > 3  # recurring across multiple days/hours
                
                causes.append(AttributedCause(
                    cause_id=f"CAUSE-{asset_id}-THERMAL-TRIP",
                    category="equipment_fault",
                    title=f"{asset_id} High Temperature Thermal Derate & Trip",
                    description=f"Inverter {asset_id} suffered repeated IGBT module thermal trips reaching up to {max_temp:.1f}°C during peak solar irradiance. Generation loss verified against peer inverters.",
                    asset_id=asset_id,
                    attributed_loss_mwh=total_loss_mwh,
                    attributed_financial_loss_usd=financial_loss,
                    share_of_variance_pct=0.0,  # Computed in reconciliation
                    calculation_method="peer_asset_benchmark_delta",
                    confidence_basis="high_sensor_evidence_and_alarms",
                    confidence_score=0.96,
                    attribution_status="confirmed",
                    predictability="unplanned",
                    controllability="controllable",
                    recurrence="recurring" if is_recurring else "one_off",
                    severity="critical" if total_loss_mwh > 20.0 else "high",
                    evidence=evidence_list
                ))

        return causes

    def _attribute_grid_curtailment(self, start_time: datetime, end_time: datetime, tariff: float) -> List[AttributedCause]:
        """
        Attributes losses to grid operator / ISO curtailment directives.
        """
        causes = []
        curt_events = self.db.query(ExternalEvent).filter(
            ExternalEvent.plant_id == self.plant_id,
            ExternalEvent.timestamp_start <= end_time,
            ExternalEvent.timestamp_end >= start_time,
            ExternalEvent.event_type == "grid_curtailment"
        ).all()

        for ev in curt_events:
            ev_start = max(ev.timestamp_start, start_time)
            ev_end = min(ev.timestamp_end, end_time)
            dur_hours = max(0.0, (ev_end - ev_start).total_seconds() / 3600.0)
            lost_mwh = round(ev.curtailed_capacity_mw * dur_hours, 2)

            if lost_mwh > 0.05:
                causes.append(AttributedCause(
                    cause_id=f"CAUSE-GRID-CURT-{ev.id}",
                    category="grid_curtailment",
                    title=f"ISO Grid Dispatch Curtailment ({ev.iso_directive_code or 'Direct Order'})",
                    description=f"System operator ordered {ev.curtailed_capacity_mw} MW active power curtailment due to regional transmission bottleneck.",
                    asset_id=None,
                    attributed_loss_mwh=lost_mwh,
                    attributed_financial_loss_usd=round(lost_mwh * tariff, 2),
                    share_of_variance_pct=0.0,
                    calculation_method="curtailed_capacity_duration_integration",
                    confidence_basis="direct_curtailment_order",
                    confidence_score=0.99,
                    attribution_status="confirmed",
                    predictability="unplanned",
                    controllability="uncontrollable",
                    recurrence="intermittent",
                    severity="medium",
                    evidence=[
                        EvidenceReference(
                            source_type="iso_directive",
                            source_id=str(ev.iso_directive_code or f"EV-{ev.id}"),
                            record_timestamp=ev.timestamp_start,
                            metric_name="curtailed_capacity_mw",
                            metric_value=f"{ev.curtailed_capacity_mw} MW",
                            baseline_value="50.0 MW Maximum Export Capacity",
                            description=f"ISO order: {ev.impact_description or 'Regional transmission congestion'}"
                        )
                    ]
                ))

        return causes

    def _attribute_weather_variance(self, start_time: datetime, end_time: datetime, tariff: float, expected_mwh: float) -> List[AttributedCause]:
        """
        Attributes generation shortfall due to weather (actual GHI < forecasted GHI).
        """
        causes = []

        # Compare observed GHI vs forecast GHI during daylight hours
        obs_recs = {
            w.timestamp: w.ghi_wm2
            for w in self.db.query(WeatherRecord).filter(
                WeatherRecord.plant_id == self.plant_id,
                WeatherRecord.timestamp >= start_time,
                WeatherRecord.timestamp <= end_time,
                WeatherRecord.data_type == "observed"
            ).all()
        }

        fore_recs = {
            w.timestamp: w.ghi_wm2
            for w in self.db.query(WeatherRecord).filter(
                WeatherRecord.plant_id == self.plant_id,
                WeatherRecord.timestamp >= start_time,
                WeatherRecord.timestamp <= end_time,
                WeatherRecord.data_type == "forecast"
            ).all()
        }

        if not obs_recs or not fore_recs:
            return causes

        total_weather_loss_mwh = 0.0
        evidence_list: List[EvidenceReference] = []

        for ts, fore_ghi in fore_recs.items():
            if fore_ghi and fore_ghi > 60.0:  # Daylight threshold
                obs_ghi = obs_recs.get(ts, fore_ghi)
                if obs_ghi is not None and obs_ghi < fore_ghi:
                    ghi_delta = fore_ghi - obs_ghi
                    # Physical conversion: 1000 W/m2 ~ 50 MW plant capacity -> 1 W/m2 ~ 0.05 MW
                    hourly_shortfall_mwh = (ghi_delta / 1000.0) * (settings.PLANT_CAPACITY_MW * 0.85)
                    total_weather_loss_mwh += hourly_shortfall_mwh

                    if len(evidence_list) < 2 and ghi_delta > 150.0:
                        evidence_list.append(EvidenceReference(
                            source_type="weather_pyranometer",
                            source_id=f"MET01-{ts.strftime('%Y%m%d%H')}",
                            record_timestamp=ts,
                            metric_name="ghi_wm2",
                            metric_value=f"{obs_ghi:.0f} W/m² (Observed)",
                            baseline_value=f"{fore_ghi:.0f} W/m² (Day-Ahead Forecast)",
                            description=f"Cloud cover attenuation reduced surface solar irradiance by {ghi_delta:.0f} W/m²."
                        ))

        total_weather_loss_mwh = round(total_weather_loss_mwh, 2)
        if total_weather_loss_mwh > 0.5:
            causes.append(AttributedCause(
                cause_id="CAUSE-WEATHER-SOLAR-IRRADIANCE",
                category="weather",
                title="Cloud Cover & Atmospheric Solar Irradiance Deficit",
                description=f"Observed Global Horizontal Irradiance (GHI) fell below Day-Ahead forecast due to localized cloud cover, causing {total_weather_loss_mwh} MWh deficit.",
                asset_id=None,
                attributed_loss_mwh=total_weather_loss_mwh,
                attributed_financial_loss_usd=round(total_weather_loss_mwh * tariff, 2),
                share_of_variance_pct=0.0,
                calculation_method="pyranometer_irradiance_deficit_model",
                confidence_basis="pyranometer_and_open_meteo_readings",
                confidence_score=0.92,
                attribution_status="confirmed",
                predictability="force_majeure",
                controllability="uncontrollable",
                recurrence="intermittent",
                severity="medium",
                evidence=evidence_list
            ))

        return causes

    def _attribute_maintenance(self, start_time: datetime, end_time: datetime, tariff: float) -> List[AttributedCause]:
        """
        Attributes planned or corrective maintenance downtime during daylight hours.
        """
        causes = []
        maint_recs = self.db.query(MaintenanceRecord).filter(
            MaintenanceRecord.plant_id == self.plant_id,
            MaintenanceRecord.scheduled_start <= end_time,
            MaintenanceRecord.scheduled_end >= start_time,
            MaintenanceRecord.downtime_hours > 0.0
        ).all()

        for m in maint_recs:
            # 5 MW inverter capacity * downtime hours * capacity factor ~ 0.65 during daytime
            loss_mwh = round(m.downtime_hours * 5.0 * 0.65, 2)
            if loss_mwh > 0.1:
                causes.append(AttributedCause(
                    cause_id=f"CAUSE-MAINT-{m.work_order_id}",
                    category="maintenance",
                    title=f"Maintenance Downtime: {m.procedure_code} ({m.asset_id})",
                    description=f"{m.maintenance_type.capitalize()} maintenance logged by {m.technician_in_charge}. Outage duration: {m.downtime_hours}h.",
                    asset_id=m.asset_id,
                    attributed_loss_mwh=loss_mwh,
                    attributed_financial_loss_usd=round(loss_mwh * tariff, 2),
                    share_of_variance_pct=0.0,
                    calculation_method="scheduled_outage_capacity_integration",
                    confidence_basis="technician_work_order_logs",
                    confidence_score=0.95,
                    attribution_status="confirmed",
                    predictability="planned" if m.maintenance_type == "preventative" else "unplanned",
                    controllability="controllable",
                    recurrence="one_off",
                    severity="low",
                    evidence=[
                        EvidenceReference(
                            source_type="maintenance_log",
                            source_id=m.work_order_id,
                            record_timestamp=m.scheduled_start,
                            metric_name="downtime_hours",
                            metric_value=f"{m.downtime_hours} hours",
                            baseline_value="0.0 hours (Normal Operation)",
                            description=f"Procedure: {m.procedure_description or m.procedure_code}"
                        )
                    ]
                ))

        return causes

    def _build_waterfall_steps(self, expected_mwh: float, actual_mwh: float, causes: List[AttributedCause]) -> List[Dict[str, Any]]:
        """
        Builds steps for waterfall chart:
        Baseline (Expected) -> Cause 1 (-) -> Cause 2 (-) -> ... -> Residual (-) -> Actual
        """
        steps = [
            {"name": "Forecast Baseline", "value": round(expected_mwh, 2), "type": "baseline"}
        ]
        
        running_total = expected_mwh
        for c in causes:
            delta = -c.attributed_loss_mwh
            running_total += delta
            steps.append({
                "name": c.title[:24] + ("..." if len(c.title) > 24 else ""),
                "delta": round(delta, 2),
                "value": round(running_total, 2),
                "category": c.category,
                "type": "cause"
            })

        steps.append({
            "name": "Actual Output",
            "value": round(actual_mwh, 2),
            "type": "actual"
        })

        return steps
