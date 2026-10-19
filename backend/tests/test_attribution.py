import pytest
from datetime import datetime, timedelta
from app.ingestion.pipeline import IngestionPipeline
from app.attribution.engine import VarianceAttributionEngine
from app.models.generation import GenerationRecord
from app.models.forecast import ForecastRecord
from app.models.equipment import EquipmentTelemetry
from app.models.external_events import ExternalEvent
from app.models.financial import FinancialAssumption

def test_attribution_reconciliation_and_residual(db):
    pipeline = IngestionPipeline(db)
    dt1 = datetime(2026, 10, 20, 12, 0, 0)
    dt2 = datetime(2026, 10, 20, 13, 0, 0)

    # 1. Setup financial assumption
    db.add(FinancialAssumption(
        plant_id="helios-50",
        effective_date=datetime(2026, 10, 20).date(),
        ppa_tariff_usd_per_mwh=50.0,
        om_hourly_cost_usd=100.0,
        curtailment_compensation_usd_per_mwh=40.0,
        budgeted_monthly_generation_mwh=8000.0,
        budgeted_monthly_revenue_usd=400000.0,
        budgeted_monthly_opex_usd=30000.0,
        source_file="fin.csv",
        source_row_index=1,
        ingestion_batch_id="BATCH-TEST"
    ))

    # 2. Forecast: Expected 40.0 MW at hour 12
    db.add(ForecastRecord(
        plant_id="helios-50",
        forecast_version="day_ahead_v1",
        forecast_horizon="day_ahead",
        target_timestamp=dt1,
        expected_mw=40.0,
        expected_mwh=40.0,
        source_file="test.csv",
        source_row_index=1,
        ingestion_batch_id="BATCH-TEST"
    ))

    # 3. Actual plant output: 25.0 MW (Shortfall of 15.0 MWh)
    db.add(GenerationRecord(
        plant_id="helios-50",
        asset_id=None,
        timestamp=dt1,
        actual_mw=25.0,
        actual_mwh=25.0,
        source_file="test.csv",
        source_row_index=1,
        ingestion_batch_id="BATCH-TEST"
    ))

    # 4. Equipment telemetry: Inverter 04 tripped with alarm
    # Other inverters producing 2.77 MW average
    for i in range(1, 11):
        inv_id = f"INV-{i:02d}"
        if i == 4:
            # Tripped
            db.add(EquipmentTelemetry(
                asset_id=inv_id,
                timestamp=dt1,
                ac_power_kw=0.0,
                inverter_temp_c=74.0,
                operating_state="fault_trip",
                alarm_code="INV_ALARM_OVERTEMP",
                source_file="telem.csv",
                source_row_index=i,
                ingestion_batch_id="BATCH-TEST"
            ))
        else:
            db.add(EquipmentTelemetry(
                asset_id=inv_id,
                timestamp=dt1,
                ac_power_kw=2777.0,
                inverter_temp_c=50.0,
                operating_state="running",
                source_file="telem.csv",
                source_row_index=i,
                ingestion_batch_id="BATCH-TEST"
            ))

    # 5. Grid curtailment event: 5 MW curtailment
    db.add(ExternalEvent(
        plant_id="helios-50",
        timestamp_start=dt1,
        timestamp_end=dt2,
        event_type="grid_curtailment",
        curtailed_capacity_mw=5.0,
        iso_directive_code="CAISO-TEST-01",
        source_file="events.csv",
        source_row_index=1,
        ingestion_batch_id="BATCH-TEST"
    ))

    db.commit()

    # Execute attribution
    engine = VarianceAttributionEngine(db, "helios-50")
    report = engine.attribute_variance(dt1, dt2, "day_ahead_v1")

    assert report.expected_mwh == 40.0
    assert report.actual_mwh == 25.0
    assert report.total_variance_mwh == -15.0
    assert report.reconciliation_valid is True
    assert report.reconciliation_discrepancy_mwh <= 0.05

    # Check causes
    categories = [c.category for c in report.causes]
    assert "equipment_fault" in categories
    assert "grid_curtailment" in categories
    assert "unexplained_residual" in categories

    # Sum of all attributed + residual must equal total variance loss
    total_reconciled = report.total_attributed_loss_mwh + report.unexplained_residual_mwh
    assert abs(total_reconciled - 15.0) <= 0.05
