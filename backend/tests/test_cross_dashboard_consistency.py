import pytest
from datetime import datetime, date, timedelta
from app.ingestion.pipeline import IngestionPipeline
from app.analytics.deterministic import DeterministicAnalyticsEngine
from app.api.v1.dashboards import get_executive_dashboard, get_operations_dashboard, get_technician_dashboard
from app.auth.rbac import UserRole
from app.models.generation import GenerationRecord
from app.models.forecast import ForecastRecord
from app.models.financial import FinancialAssumption

@pytest.mark.asyncio
async def test_kpi_consistency_across_three_dashboards(db):
    pipeline = IngestionPipeline(db)
    start_t = datetime(2026, 10, 15, 0, 0, 0)
    end_t = datetime(2026, 10, 15, 23, 0, 0)

    # Seed financial assumption
    db.add(FinancialAssumption(
        plant_id="helios-50",
        effective_date=date(2026, 10, 15),
        ppa_tariff_usd_per_mwh=48.50,
        om_hourly_cost_usd=120.0,
        curtailment_compensation_usd_per_mwh=40.0,
        budgeted_monthly_generation_mwh=8500.0,
        budgeted_monthly_revenue_usd=412250.0,
        budgeted_monthly_opex_usd=38000.0,
        source_file="test.csv",
        source_row_index=1,
        ingestion_batch_id="TEST"
    ))

    # Seed forecast & generation
    db.add(ForecastRecord(
        plant_id="helios-50",
        forecast_version="day_ahead_v1",
        target_timestamp=datetime(2026, 10, 15, 12, 0, 0),
        expected_mw=45.0,
        expected_mwh=45.0,
        source_file="test.csv",
        source_row_index=1,
        ingestion_batch_id="TEST"
    ))
    db.add(GenerationRecord(
        plant_id="helios-50",
        asset_id=None,
        timestamp=datetime(2026, 10, 15, 12, 0, 0),
        actual_mw=38.0,
        actual_mwh=38.0,
        source_file="test.csv",
        source_row_index=1,
        ingestion_batch_id="TEST"
    ))
    db.commit()

    # Query all three dashboards
    exec_resp = await get_executive_dashboard(
        plant_id="helios-50",
        start_time=start_t,
        end_time=end_t,
        forecast_version="day_ahead_v1",
        db=db,
        current_role=UserRole.CEO
    )

    ops_resp = await get_operations_dashboard(
        plant_id="helios-50",
        start_time=start_t,
        end_time=end_t,
        forecast_version="day_ahead_v1",
        db=db,
        current_role=UserRole.OPERATIONS
    )

    tech_resp = await get_technician_dashboard(
        plant_id="helios-50",
        start_time=start_t,
        end_time=end_t,
        forecast_version="day_ahead_v1",
        db=db,
        current_role=UserRole.TECHNICIAN
    )

    # 1. Compare Expected MWh
    assert exec_resp.kpi.expected_generation_mwh == ops_resp.kpi.expected_generation_mwh == tech_resp.kpi.expected_generation_mwh == 45.0

    # 2. Compare Actual MWh
    assert exec_resp.kpi.actual_generation_mwh == ops_resp.kpi.actual_generation_mwh == tech_resp.kpi.actual_generation_mwh == 38.0

    # 3. Compare Variance MWh
    assert exec_resp.kpi.variance_mwh == ops_resp.kpi.variance_mwh == tech_resp.kpi.variance_mwh == -7.0

    # 4. Compare Capacity Factor %
    assert exec_resp.kpi.capacity_factor_pct == ops_resp.kpi.capacity_factor_pct == tech_resp.kpi.capacity_factor_pct

    # 5. Compare Availability %
    assert exec_resp.kpi.availability_pct == ops_resp.kpi.availability_pct == tech_resp.kpi.availability_pct

    # 6. Compare Financial Values
    assert exec_resp.kpi.realized_revenue_usd == ops_resp.kpi.realized_revenue_usd == tech_resp.kpi.realized_revenue_usd
    assert exec_resp.kpi.lost_revenue_usd == ops_resp.kpi.lost_revenue_usd == tech_resp.kpi.lost_revenue_usd
