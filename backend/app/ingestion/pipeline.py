import io
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.plant import Plant, Asset
from app.models.generation import GenerationRecord
from app.models.forecast import ForecastRecord
from app.models.equipment import EquipmentTelemetry
from app.models.weather import WeatherRecord
from app.models.workforce import WorkforceRecord
from app.models.maintenance import MaintenanceRecord
from app.models.financial import FinancialAssumption
from app.models.external_events import ExternalEvent
from app.models.quarantine import IngestionBatch, QuarantineRecord
from app.ingestion.validator import DataValidator
from app.schemas.ingestion import IngestionReport, QuarantineItem

class IngestionPipeline:
    def __init__(self, db: Session):
        self.db = db

    def _extract_field(self, row: Any, keys: List[str]) -> Optional[Any]:
        for k in keys:
            if k in row and row[k] is not None and not pd.isna(row[k]):
                return row[k]
        return None

    def ensure_default_plant_and_assets(self, plant_id: str = "helios-50") -> Plant:
        """
        Ensures the canonical 50 MW solar plant and its inverters exist in DB.
        """
        plant = self.db.query(Plant).filter(Plant.id == plant_id).first()
        if not plant:
            plant = Plant(
                id=plant_id,
                name="Helios-50 Solar Farm",
                capacity_mw=50.0,
                technology="solar_pv",
                latitude=34.0522,
                longitude=-117.2437,
                timezone="America/Los_Angeles"
            )
            self.db.add(plant)
            self.db.flush()

            # Create 10 inverters (5 MW each = 50 MW total)
            for i in range(1, 11):
                inv = Asset(
                    id=f"INV-{i:02d}",
                    plant_id=plant_id,
                    name=f"Central Inverter Unit {i:02d}",
                    asset_type="inverter",
                    capacity_kw=5000.0,
                    model="SMA-SunnyCentral-5000",
                    status="operational"
                )
                self.db.add(inv)

            # Create on-site pyranometer weather station
            met = Asset(
                id="MET-01",
                plant_id=plant_id,
                name="Main Substation Meteorological Station",
                asset_type="pyranometer",
                capacity_kw=0.0,
                model="Kipp & Zonen CMP11",
                status="operational"
            )
            self.db.add(met)

            # Create main step-up transformer
            tx = Asset(
                id="TX-01",
                plant_id=plant_id,
                name="34.5kV / 230kV Main Step-Up Transformer",
                asset_type="transformer",
                capacity_kw=55000.0,
                model="ABB Power-55MVA",
                status="operational"
            )
            self.db.add(tx)
            self.db.commit()

        return plant

    def ingest_csv(
        self,
        file_content: str,
        filename: str,
        file_type: str,
        plant_id: str = "helios-50"
    ) -> IngestionReport:
        """
        Parses, validates, normalizes, and ingests CSV content into canonical tables.
        Invalid rows are quarantined with detailed provenance.
        """
        self.ensure_default_plant_and_assets(plant_id)
        batch_id = f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        try:
            df = pd.read_csv(io.StringIO(file_content))
        except Exception as e:
            # Entire file malformed
            q = QuarantineRecord(
                batch_id=batch_id,
                source_file=filename,
                row_index=0,
                raw_content=file_content[:500],
                error_type="malformed_csv",
                error_detail=f"CSV parser error: {str(e)}"
            )
            self.db.add(q)
            batch = IngestionBatch(
                batch_id=batch_id,
                source_file=filename,
                file_type=file_type,
                total_records=0,
                valid_records=0,
                quarantined_records=1,
                status="failed",
                summary=f"Failed to parse CSV file: {str(e)}"
            )
            self.db.add(batch)
            self.db.commit()
            return IngestionReport(
                batch_id=batch_id,
                source_file=filename,
                file_type=file_type,
                total_records=0,
                valid_records=0,
                quarantined_records=1,
                success_rate_pct=0.0,
                status="failed",
                quarantined_items=[QuarantineItem(
                    id=1, source_file=filename, row_index=0, raw_content=file_content[:200],
                    error_type="malformed_csv", error_detail=str(e), quarantined_at=datetime.utcnow()
                )],
                created_at=datetime.utcnow(),
                summary=f"Failed to parse CSV file: {str(e)}"
            )

        total_records = len(df)
        valid_count = 0
        quarantine_items: List[QuarantineItem] = []

        # Route by file_type
        if file_type == "generation":
            valid_count, quarantine_items = self._ingest_generation(df, filename, batch_id, plant_id)
        elif file_type == "forecast":
            valid_count, quarantine_items = self._ingest_forecast(df, filename, batch_id, plant_id)
        elif file_type == "equipment":
            valid_count, quarantine_items = self._ingest_equipment(df, filename, batch_id, plant_id)
        elif file_type == "weather":
            valid_count, quarantine_items = self._ingest_weather(df, filename, batch_id, plant_id)
        elif file_type == "workforce":
            valid_count, quarantine_items = self._ingest_workforce(df, filename, batch_id, plant_id)
        elif file_type == "maintenance":
            valid_count, quarantine_items = self._ingest_maintenance(df, filename, batch_id, plant_id)
        elif file_type == "financial":
            valid_count, quarantine_items = self._ingest_financial(df, filename, batch_id, plant_id)
        elif file_type == "external_events":
            valid_count, quarantine_items = self._ingest_external_events(df, filename, batch_id, plant_id)
        else:
            # Unknown file type
            for idx, row in df.iterrows():
                q = QuarantineRecord(
                    batch_id=batch_id,
                    source_file=filename,
                    row_index=int(idx) + 1,
                    raw_content=json.dumps(row.to_dict(), default=str),
                    error_type="unknown_file_type",
                    error_detail=f"Unsupported file type '{file_type}'"
                )
                self.db.add(q)
                quarantine_items.append(QuarantineItem(
                    id=0, source_file=filename, row_index=int(idx) + 1,
                    raw_content=str(row.to_dict()), error_type="unknown_file_type",
                    error_detail=f"Unsupported file type '{file_type}'",
                    quarantined_at=datetime.utcnow()
                ))

        quarantined_count = len(quarantine_items)
        success_rate = (valid_count / total_records * 100.0) if total_records > 0 else 0.0
        status = "completed" if quarantined_count == 0 else ("partial" if valid_count > 0 else "failed")
        summary_msg = f"Ingested {valid_count} valid records, quarantined {quarantined_count} invalid records ({success_rate:.1f}% success)."

        batch_record = IngestionBatch(
            batch_id=batch_id,
            source_file=filename,
            file_type=file_type,
            total_records=total_records,
            valid_records=valid_count,
            quarantined_records=quarantined_count,
            status=status,
            summary=summary_msg
        )
        self.db.add(batch_record)
        self.db.commit()

        return IngestionReport(
            batch_id=batch_id,
            source_file=filename,
            file_type=file_type,
            total_records=total_records,
            valid_records=valid_count,
            quarantined_records=quarantined_count,
            success_rate_pct=round(success_rate, 2),
            status=status,
            quarantined_items=quarantine_items[:50],  # Return up to first 50 quarantined items in response
            created_at=datetime.utcnow(),
            summary=summary_msg
        )

    def _ingest_generation(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []
        seen_keys = set()

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            # Check timestamp
            ts_raw = row.get("timestamp") or row.get("datetime") or row.get("time")
            ts, err = DataValidator.normalize_timestamp(ts_raw)
            if err:
                self._quarantine(batch_id, filename, row_idx, raw_json, "timestamp_error", err, quarantine_items)
                continue

            # Asset ID (optional for plant-level, mandatory for inverter-level)
            asset_raw = row.get("asset_id") or row.get("inverter_id")
            asset_id, _ = DataValidator.normalize_asset_id(asset_raw)
            if asset_id:
                asset_obj = self.db.query(Asset).filter(Asset.id == asset_id, Asset.plant_id == plant_id).first()
                if not asset_obj:
                    self._quarantine(batch_id, filename, row_idx, raw_json, "invalid_asset_reference", f"Asset {asset_id} does not exist in plant registry", quarantine_items)
                    continue
            
            # Key for duplicate check
            key = (plant_id, asset_id, ts)
            if key in seen_keys:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_in_file", f"Duplicate row for {key}", quarantine_items)
                continue
            seen_keys.add(key)

            # Check actual_mw or actual_mwh without python falsy trap on 0.0
            mw_raw = self._extract_field(row, ["actual_mw", "generation_mw", "power_mw"])
            mwh_raw = self._extract_field(row, ["actual_mwh", "energy_mwh"])

            actual_mw, err_mw = (None, None)
            actual_mwh, err_mwh = (None, None)

            if mw_raw is not None and not pd.isna(mw_raw):
                actual_mw, err_mw = DataValidator.normalize_float(mw_raw, "actual_mw", min_val=0.0, max_val=100.0)
            
            if mwh_raw is not None and not pd.isna(mwh_raw):
                actual_mwh, err_mwh = DataValidator.normalize_float(mwh_raw, "actual_mwh", min_val=0.0, max_val=100.0)

            # Handle unit conversion if kW or kWh provided
            if actual_mw is None and "actual_kw" in row:
                actual_mw, err_mw = DataValidator.normalize_float(row.get("actual_kw"), "actual_kw", unit_from="kw", unit_to="mw")
            if actual_mwh is None and "actual_kwh" in row:
                actual_mwh, err_mwh = DataValidator.normalize_float(row.get("actual_kwh"), "actual_kwh", unit_from="kwh", unit_to="mwh")

            # Fallbacks: 1-hour interval implies MW = MWh
            if actual_mw is not None and actual_mwh is None:
                actual_mwh = actual_mw
            elif actual_mwh is not None and actual_mw is None:
                actual_mw = actual_mwh

            if actual_mw is None or actual_mwh is None:
                err_msg = err_mw or err_mwh or "Missing generation values"
                self._quarantine(batch_id, filename, row_idx, raw_json, "missing_generation_value", err_msg, quarantine_items)
                continue

            # DB duplicate check
            existing = self.db.query(GenerationRecord).filter(
                GenerationRecord.plant_id == plant_id,
                GenerationRecord.asset_id == asset_id,
                GenerationRecord.timestamp == ts
            ).first()

            if existing:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_db_record", f"Record for {key} already exists in database", quarantine_items)
                continue

            rec = GenerationRecord(
                plant_id=plant_id,
                asset_id=asset_id,
                timestamp=ts,
                actual_mw=actual_mw,
                actual_mwh=actual_mwh,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_forecast(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []
        seen_keys = set()

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            ts_raw = row.get("target_timestamp") or row.get("timestamp") or row.get("datetime")
            target_ts, err = DataValidator.normalize_timestamp(ts_raw)
            if err:
                self._quarantine(batch_id, filename, row_idx, raw_json, "timestamp_error", err, quarantine_items)
                continue

            forecast_version = str(row.get("forecast_version", "day_ahead_v1")).strip()
            horizon = str(row.get("forecast_horizon", "day_ahead")).strip()
            
            key = (plant_id, forecast_version, target_ts)
            if key in seen_keys:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_forecast_in_file", f"Duplicate forecast for {key}", quarantine_items)
                continue
            seen_keys.add(key)

            mw_raw = self._extract_field(row, ["expected_mw", "forecast_mw"])
            mwh_raw = self._extract_field(row, ["expected_mwh", "forecast_mwh"])

            expected_mw, err_mw = DataValidator.normalize_float(mw_raw, "expected_mw", min_val=0.0, max_val=100.0)
            if err_mw:
                self._quarantine(batch_id, filename, row_idx, raw_json, "invalid_expected_mw", err_mw, quarantine_items)
                continue

            expected_mwh = expected_mw if mwh_raw is None or pd.isna(mwh_raw) else float(mwh_raw)
            ghi_exp = float(row.get("ghi_expected_wm2")) if row.get("ghi_expected_wm2") is not None and not pd.isna(row.get("ghi_expected_wm2")) else None

            # DB duplicate check
            existing = self.db.query(ForecastRecord).filter(
                ForecastRecord.plant_id == plant_id,
                ForecastRecord.forecast_version == forecast_version,
                ForecastRecord.target_timestamp == target_ts
            ).first()

            if existing:
                self._quarantine(batch_id, filename, row_idx, raw_json, "forecast_version_immutable", f"Forecast version {forecast_version} already stored for {target_ts}. Preserving historical forecast without overwrite.", quarantine_items)
                continue

            rec = ForecastRecord(
                plant_id=plant_id,
                forecast_version=forecast_version,
                forecast_horizon=horizon,
                forecast_generated_at=datetime.utcnow(),
                target_timestamp=target_ts,
                expected_mw=expected_mw,
                expected_mwh=expected_mwh,
                ghi_expected_wm2=ghi_exp,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_equipment(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []
        seen_keys = set()

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            ts_raw = row.get("timestamp") or row.get("datetime")
            ts, err = DataValidator.normalize_timestamp(ts_raw)
            if err:
                self._quarantine(batch_id, filename, row_idx, raw_json, "timestamp_error", err, quarantine_items)
                continue

            asset_raw = row.get("asset_id") or row.get("inverter_id")
            asset_id, _ = DataValidator.normalize_asset_id(asset_raw)
            if not asset_id:
                self._quarantine(batch_id, filename, row_idx, raw_json, "missing_asset_id", "Equipment telemetry requires valid asset_id", quarantine_items)
                continue

            # Verify asset exists
            asset_obj = self.db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset_obj:
                self._quarantine(batch_id, filename, row_idx, raw_json, "invalid_asset_reference", f"Asset {asset_id} does not exist in plant registry", quarantine_items)
                continue

            key = (asset_id, ts)
            if key in seen_keys:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_telemetry", f"Duplicate telemetry for {key}", quarantine_items)
                continue
            seen_keys.add(key)

            temp = float(row.get("inverter_temp_c")) if row.get("inverter_temp_c") is not None and not pd.isna(row.get("inverter_temp_c")) else None
            dc_kw = float(row.get("dc_power_kw")) if row.get("dc_power_kw") is not None and not pd.isna(row.get("dc_power_kw")) else None
            ac_kw = float(row.get("ac_power_kw")) if row.get("ac_power_kw") is not None and not pd.isna(row.get("ac_power_kw")) else None
            v = float(row.get("dc_voltage_v")) if row.get("dc_voltage_v") is not None and not pd.isna(row.get("dc_voltage_v")) else None
            i = float(row.get("dc_current_a")) if row.get("dc_current_a") is not None and not pd.isna(row.get("dc_current_a")) else None
            eff = float(row.get("efficiency_pct")) if row.get("efficiency_pct") is not None and not pd.isna(row.get("efficiency_pct")) else (round(ac_kw / dc_kw * 100.0, 2) if dc_kw and ac_kw and dc_kw > 0 else None)
            
            state = str(row.get("operating_state", "running")).strip().lower()
            raw_alarm = row.get("alarm_code")
            alarm_code = str(raw_alarm).strip() if (raw_alarm is not None and not pd.isna(raw_alarm) and str(raw_alarm).strip().lower() not in ["", "nan", "none", "null"]) else None
            raw_desc = row.get("alarm_description")
            alarm_desc = str(raw_desc).strip() if (raw_desc is not None and not pd.isna(raw_desc) and str(raw_desc).strip().lower() not in ["", "nan", "none", "null"]) else None

            existing = self.db.query(EquipmentTelemetry).filter(
                EquipmentTelemetry.asset_id == asset_id,
                EquipmentTelemetry.timestamp == ts
            ).first()

            if existing:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_db_telemetry", f"Telemetry for {asset_id} at {ts} already exists", quarantine_items)
                continue

            rec = EquipmentTelemetry(
                asset_id=asset_id,
                timestamp=ts,
                dc_power_kw=dc_kw,
                ac_power_kw=ac_kw,
                dc_voltage_v=v,
                dc_current_a=i,
                inverter_temp_c=temp,
                efficiency_pct=eff,
                operating_state=state,
                alarm_code=alarm_code,
                alarm_description=alarm_desc,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_weather(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []
        seen_keys = set()

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            ts_raw = row.get("timestamp") or row.get("datetime")
            ts, err = DataValidator.normalize_timestamp(ts_raw)
            if err:
                self._quarantine(batch_id, filename, row_idx, raw_json, "timestamp_error", err, quarantine_items)
                continue

            data_type = str(row.get("data_type", "observed")).strip().lower()
            if data_type not in ["observed", "forecast", "estimated", "unavailable"]:
                data_type = "observed"

            key = (plant_id, ts, data_type)
            if key in seen_keys:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_weather", f"Duplicate weather record for {key}", quarantine_items)
                continue
            seen_keys.add(key)

            ghi = float(row.get("ghi_wm2")) if row.get("ghi_wm2") is not None and not pd.isna(row.get("ghi_wm2")) else None
            dni = float(row.get("dni_wm2")) if row.get("dni_wm2") is not None and not pd.isna(row.get("dni_wm2")) else None
            dhi = float(row.get("dhi_wm2")) if row.get("dhi_wm2") is not None and not pd.isna(row.get("dhi_wm2")) else None
            amb_temp = float(row.get("ambient_temp_c")) if row.get("ambient_temp_c") is not None and not pd.isna(row.get("ambient_temp_c")) else None
            cell_temp = float(row.get("cell_temp_c")) if row.get("cell_temp_c") is not None and not pd.isna(row.get("cell_temp_c")) else None
            wind_speed = float(row.get("wind_speed_ms")) if row.get("wind_speed_ms") is not None and not pd.isna(row.get("wind_speed_ms")) else None
            cloud = float(row.get("cloud_cover_pct")) if row.get("cloud_cover_pct") is not None and not pd.isna(row.get("cloud_cover_pct")) else None

            existing = self.db.query(WeatherRecord).filter(
                WeatherRecord.plant_id == plant_id,
                WeatherRecord.timestamp == ts,
                WeatherRecord.data_type == data_type
            ).first()

            if existing:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_db_weather", f"Weather record for {ts} ({data_type}) already exists in DB", quarantine_items)
                continue

            rec = WeatherRecord(
                plant_id=plant_id,
                timestamp=ts,
                ghi_wm2=ghi,
                dni_wm2=dni,
                dhi_wm2=dhi,
                ambient_temp_c=amb_temp,
                cell_temp_c=cell_temp,
                wind_speed_ms=wind_speed,
                cloud_cover_pct=cloud,
                data_type=data_type,
                source_provider=str(row.get("source_provider", "open-meteo")),
                provenance_notes=str(row.get("provenance_notes", "Historical solar irradiance observation")),
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_workforce(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []
        seen_keys = set()

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            date_raw = row.get("date")
            try:
                rec_date = pd.to_datetime(date_raw).date()
            except Exception as e:
                self._quarantine(batch_id, filename, row_idx, raw_json, "date_format_error", f"Invalid date: {str(e)}", quarantine_items)
                continue

            shift = str(row.get("shift", "morning")).strip().lower()
            key = (plant_id, rec_date, shift)
            if key in seen_keys:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_workforce", f"Duplicate workforce entry for {key}", quarantine_items)
                continue
            seen_keys.add(key)

            tech_count = int(row.get("technicians_on_site", 2))
            hours = float(row.get("hours_logged", 8.0))
            lead = str(row.get("lead_technician", "Carlos Mendez"))
            roster = str(row.get("technician_roster", ""))
            certs = str(row.get("skill_certifications", "HV_Certified"))
            notes = str(row.get("notes", ""))

            existing = self.db.query(WorkforceRecord).filter(
                WorkforceRecord.plant_id == plant_id,
                WorkforceRecord.date == rec_date,
                WorkforceRecord.shift == shift
            ).first()

            if existing:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_db_workforce", f"Workforce for {rec_date} {shift} exists", quarantine_items)
                continue

            rec = WorkforceRecord(
                plant_id=plant_id,
                date=rec_date,
                shift=shift,
                technicians_on_site=tech_count,
                hours_logged=hours,
                lead_technician=lead,
                technician_roster=roster,
                skill_certifications=certs,
                notes=notes,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_maintenance(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            wo_id = str(row.get("work_order_id", f"WO-{uuid.uuid4().hex[:6]}")).strip()
            asset_raw = row.get("asset_id")
            asset_id, _ = DataValidator.normalize_asset_id(asset_raw)
            if not asset_id:
                self._quarantine(batch_id, filename, row_idx, raw_json, "missing_asset_id", "Maintenance record requires asset_id", quarantine_items)
                continue

            # Parse scheduled start/end
            start_dt, err_s = DataValidator.normalize_timestamp(row.get("scheduled_start"))
            end_dt, err_e = DataValidator.normalize_timestamp(row.get("scheduled_end"))
            if err_s or err_e or not start_dt or not end_dt:
                self._quarantine(batch_id, filename, row_idx, raw_json, "timestamp_error", f"Invalid start/end: {err_s or err_e}", quarantine_items)
                continue

            act_start, _ = DataValidator.normalize_timestamp(row.get("actual_start"))
            act_end, _ = DataValidator.normalize_timestamp(row.get("actual_end"))
            downtime = float(row.get("downtime_hours", 0.0))
            mtype = str(row.get("maintenance_type", "corrective"))
            tech = str(row.get("technician_in_charge", "Carlos Mendez"))
            proc_code = str(row.get("procedure_code", "SOP-INV-02"))
            proc_desc = str(row.get("procedure_description", ""))
            status = str(row.get("status", "completed"))

            rec = MaintenanceRecord(
                plant_id=plant_id,
                work_order_id=wo_id,
                asset_id=asset_id,
                maintenance_type=mtype,
                scheduled_start=start_dt,
                scheduled_end=end_dt,
                actual_start=act_start,
                actual_end=act_end,
                downtime_hours=downtime,
                technician_in_charge=tech,
                procedure_code=proc_code,
                procedure_description=proc_desc,
                status=status,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_financial(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            eff_date_raw = row.get("effective_date")
            try:
                eff_date = pd.to_datetime(eff_date_raw).date()
            except Exception as e:
                self._quarantine(batch_id, filename, row_idx, raw_json, "date_format_error", f"Invalid date: {str(e)}", quarantine_items)
                continue

            ppa = float(row.get("ppa_tariff_usd_per_mwh", 48.50))
            om = float(row.get("om_hourly_cost_usd", 125.00))
            curt = float(row.get("curtailment_compensation_usd_per_mwh", 40.00))
            gen_bud = float(row.get("budgeted_monthly_generation_mwh", 8500.0))
            rev_bud = float(row.get("budgeted_monthly_revenue_usd", 412250.0))
            opex_bud = float(row.get("budgeted_monthly_opex_usd", 38000.0))

            existing = self.db.query(FinancialAssumption).filter(
                FinancialAssumption.plant_id == plant_id,
                FinancialAssumption.effective_date == eff_date
            ).first()

            if existing:
                self._quarantine(batch_id, filename, row_idx, raw_json, "duplicate_db_financial", f"Financial record for {eff_date} exists", quarantine_items)
                continue

            rec = FinancialAssumption(
                plant_id=plant_id,
                effective_date=eff_date,
                ppa_tariff_usd_per_mwh=ppa,
                om_hourly_cost_usd=om,
                curtailment_compensation_usd_per_mwh=curt,
                budgeted_monthly_generation_mwh=gen_bud,
                budgeted_monthly_revenue_usd=rev_bud,
                budgeted_monthly_opex_usd=opex_bud,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _ingest_external_events(self, df: pd.DataFrame, filename: str, batch_id: str, plant_id: str):
        valid_records = []
        quarantine_items = []

        for idx, row in df.iterrows():
            row_idx = int(idx) + 1
            raw_dict = row.to_dict()
            raw_json = json.dumps(raw_dict, default=str)

            s_dt, err_s = DataValidator.normalize_timestamp(row.get("timestamp_start"))
            e_dt, err_e = DataValidator.normalize_timestamp(row.get("timestamp_end"))
            if err_s or err_e or not s_dt or not e_dt:
                self._quarantine(batch_id, filename, row_idx, raw_json, "timestamp_error", f"Invalid event start/end: {err_s or err_e}", quarantine_items)
                continue

            etype = str(row.get("event_type", "grid_curtailment"))
            curt_mw = float(row.get("curtailed_capacity_mw", 0.0))
            iso_code = str(row.get("iso_directive_code", "CAISO-DIR-01"))
            comp_elig = str(row.get("compensation_eligible", "YES"))
            notes = str(row.get("impact_description", "Transmission congestion dispatch instruction"))

            rec = ExternalEvent(
                plant_id=plant_id,
                timestamp_start=s_dt,
                timestamp_end=e_dt,
                event_type=etype,
                curtailed_capacity_mw=curt_mw,
                iso_directive_code=iso_code,
                compensation_eligible=comp_elig,
                impact_description=notes,
                source_file=filename,
                source_row_index=row_idx,
                ingestion_batch_id=batch_id
            )
            valid_records.append(rec)

        if valid_records:
            self.db.bulk_save_objects(valid_records)
            self.db.commit()

        return len(valid_records), quarantine_items

    def _quarantine(
        self,
        batch_id: str,
        source_file: str,
        row_index: int,
        raw_content: str,
        error_type: str,
        error_detail: str,
        quarantine_items: List[QuarantineItem]
    ):
        q = QuarantineRecord(
            batch_id=batch_id,
            source_file=source_file,
            row_index=row_index,
            raw_content=raw_content,
            error_type=error_type,
            error_detail=error_detail
        )
        self.db.add(q)
        quarantine_items.append(QuarantineItem(
            id=len(quarantine_items) + 1,
            source_file=source_file,
            row_index=row_index,
            raw_content=raw_content,
            error_type=error_type,
            error_detail=error_detail,
            quarantined_at=datetime.utcnow()
        ))
