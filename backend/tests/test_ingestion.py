import pytest
from datetime import datetime
from app.ingestion.validator import DataValidator
from app.ingestion.pipeline import IngestionPipeline
from app.models.generation import GenerationRecord
from app.models.forecast import ForecastRecord
from app.models.quarantine import QuarantineRecord

def test_timestamp_normalization():
    # ISO string
    dt, err = DataValidator.normalize_timestamp("2026-10-18T14:30:00Z")
    assert err is None
    assert dt == datetime(2026, 10, 18, 14, 30, 0)

    # Standard format
    dt2, err2 = DataValidator.normalize_timestamp("2026-10-18 14:30:00")
    assert err2 is None
    assert dt2 == datetime(2026, 10, 18, 14, 30, 0)

    # Invalid timestamp
    dt_inv, err_inv = DataValidator.normalize_timestamp("NOT_A_DATE")
    assert dt_inv is None
    assert "Invalid timestamp" in err_inv or "Could not parse" in err_inv

def test_unit_conversion():
    # kW to MW
    val_mw, err = DataValidator.normalize_float(5000.0, "actual_mw", unit_from="kw", unit_to="mw")
    assert err is None
    assert val_mw == 5.0

    # Range check
    val_neg, err_neg = DataValidator.normalize_float(-10.0, "actual_mw", min_val=0.0)
    assert val_neg is None
    assert "below minimum" in err_neg

def test_asset_id_normalization():
    id1, _ = DataValidator.normalize_asset_id("inverter_04")
    assert id1 == "INV-04"

    id2, _ = DataValidator.normalize_asset_id("inv-4")
    assert id2 == "INV-04"

    id3, _ = DataValidator.normalize_asset_id("pyranometer_met")
    assert id3 == "MET-01"

def test_ingestion_and_quarantine(db):
    pipeline = IngestionPipeline(db)

    # Ingest CSV with both valid and invalid records
    csv_content = """timestamp,plant_id,asset_id,actual_mw,actual_mwh
2026-10-18T10:00:00,helios-50,INV-01,4.2,4.2
INVALID_TIMESTAMP,helios-50,INV-02,4.0,4.0
2026-10-18T11:00:00,helios-50,NON_EXISTENT_ASSET,3.5,3.5
2026-10-18T12:00:00,helios-50,INV-03,-50.0,-50.0
"""
    report = pipeline.ingest_csv(csv_content, "test_mixed.csv", "generation", "helios-50")
    assert report.total_records == 4
    assert report.valid_records == 1
    assert report.quarantined_records == 3
    assert report.status == "partial"

    # Verify quarantined records details
    q_recs = db.query(QuarantineRecord).filter(QuarantineRecord.batch_id == report.batch_id).all()
    assert len(q_recs) == 3
    error_types = [q.error_type for q in q_recs]
    assert "timestamp_error" in error_types
    assert "invalid_asset_reference" in error_types
    assert "missing_generation_value" in error_types

def test_forecast_immutable_versioning(db):
    pipeline = IngestionPipeline(db)

    # Ingest version 1
    csv_v1 = """target_timestamp,plant_id,forecast_version,forecast_horizon,expected_mw
2026-10-19T12:00:00,helios-50,day_ahead_v1,day_ahead,42.5
"""
    rep1 = pipeline.ingest_csv(csv_v1, "forecast_v1.csv", "forecast", "helios-50")
    assert rep1.valid_records == 1

    # Attempt to overwrite same version and timestamp -> Must be quarantined!
    rep_dup = pipeline.ingest_csv(csv_v1, "forecast_v1_dup.csv", "forecast", "helios-50")
    assert rep_dup.quarantined_records == 1
    assert "forecast_version_immutable" in rep_dup.quarantined_items[0].error_type

    # Ingest version 2 (e.g. intraday or updated) -> Must be accepted as separate version!
    csv_v2 = """target_timestamp,plant_id,forecast_version,forecast_horizon,expected_mw
2026-10-19T12:00:00,helios-50,intraday_v2,intraday,44.1
"""
    rep2 = pipeline.ingest_csv(csv_v2, "forecast_v2.csv", "forecast", "helios-50")
    assert rep2.valid_records == 1
