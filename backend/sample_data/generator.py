import os
import math
import random
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np

def generate_synthetic_plant_data(
    output_dir: str = "D:/Globathon/backend/sample_data",
    start_date: date = date(2026, 10, 10),
    num_days: int = 7,
    seed: int = 42
):
    """
    Generates a mathematically consistent, reproducible synthetic dataset for a 50 MW solar plant.
    Includes versioned forecasts, hourly generation, equipment telemetry, weather observations,
    workforce, maintenance, financial assumptions, and a recurring Inverter #04 thermal trip scenario.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    plant_id = "helios-50"
    num_inverters = 10
    inverter_capacity_kw = 5000.0  # 5 MW each = 50 MW
    total_capacity_mw = 50.0

    timestamps = []
    current_dt = datetime.combine(start_date, datetime.min.time())
    for d in range(num_days):
        for h in range(24):
            timestamps.append(current_dt + timedelta(days=d, hours=h))

    # --- 1. Weather Observations & Day-Ahead Forecast ---
    weather_obs = []
    forecast_da = []
    forecast_ma = []

    for ts in timestamps:
        hour = ts.hour
        day_idx = (ts.date() - start_date).days

        # Solar zenith simulation (6 AM to 6 PM daylight)
        if 6 <= hour <= 18:
            solar_elevation = math.sin((hour - 6) / 12.0 * math.pi)
            clear_sky_ghi = max(0.0, solar_elevation * 950.0)
            amb_temp = 20.0 + 15.0 * math.sin((hour - 8) / 14.0 * math.pi)
        else:
            solar_elevation = 0.0
            clear_sky_ghi = 0.0
            amb_temp = 16.0 + 3.0 * random.random()

        # Day 5 afternoon cloud cover event (12:00 to 16:00)
        cloud_factor = 1.0
        if day_idx == 4 and 12 <= hour <= 16:
            cloud_factor = 0.62  # 38% irradiance deficit

        obs_ghi = round(clear_sky_ghi * cloud_factor + (random.uniform(-10, 10) if clear_sky_ghi > 0 else 0), 1)
        obs_ghi = max(0.0, obs_ghi)
        obs_dni = round(obs_ghi * 1.15, 1) if obs_ghi > 100 else 0.0
        obs_dhi = round(obs_ghi * 0.25, 1) if obs_ghi > 50 else 0.0
        cell_temp = round(amb_temp + (obs_ghi / 800.0) * 26.0, 1) if obs_ghi > 0 else round(amb_temp, 1)

        weather_obs.append({
            "timestamp": ts.isoformat(),
            "plant_id": plant_id,
            "ghi_wm2": obs_ghi,
            "dni_wm2": obs_dni,
            "dhi_wm2": obs_dhi,
            "ambient_temp_c": round(amb_temp, 1),
            "cell_temp_c": cell_temp,
            "wind_speed_ms": round(random.uniform(1.8, 5.5), 1),
            "cloud_cover_pct": 80.0 if cloud_factor < 0.9 else round(random.uniform(5.0, 20.0), 1),
            "data_type": "observed",
            "source_provider": "pyranometer-met01",
            "provenance_notes": "SYNTHETIC: On-site Kipp & Zonen pyranometer observation"
        })

        # Forecast Day-Ahead (forecasted clear sky without knowing day 5 clouds)
        fore_da_ghi = round(clear_sky_ghi + (random.uniform(-5, 5) if clear_sky_ghi > 0 else 0), 1)
        # Expected MW = GHI / 1000 * 50 MW * derate (0.86)
        expected_mw_da = round((fore_da_ghi / 1000.0) * total_capacity_mw * 0.86, 2) if fore_da_ghi > 0 else 0.0

        forecast_da.append({
            "target_timestamp": ts.isoformat(),
            "plant_id": plant_id,
            "forecast_version": "day_ahead_v1",
            "forecast_horizon": "day_ahead",
            "expected_mw": expected_mw_da,
            "expected_mwh": expected_mw_da,  # 1 hour interval
            "ghi_expected_wm2": fore_da_ghi,
            "source_file": "forecast_day_ahead.csv",
            "source_row_index": len(forecast_da) + 1
        })

        # Month-ahead forecast (slightly coarser)
        expected_mw_ma = round((clear_sky_ghi / 1000.0) * total_capacity_mw * 0.84, 2) if clear_sky_ghi > 0 else 0.0
        forecast_ma.append({
            "target_timestamp": ts.isoformat(),
            "plant_id": plant_id,
            "forecast_version": "month_ahead_v1",
            "forecast_horizon": "month_ahead",
            "expected_mw": expected_mw_ma,
            "expected_mwh": expected_mw_ma,
            "ghi_expected_wm2": round(clear_sky_ghi, 1),
            "source_file": "forecast_month_ahead.csv",
            "source_row_index": len(forecast_ma) + 1
        })

    # --- 2. Equipment Telemetry and Generation ---
    # Recurring Fault Scenario:
    # On Days 2, 3, 4, 5, Inverter INV-04 cooling fan fails during peak hours (11:00 to 14:00).
    # Its temperature exceeds 70°C, triggering INV_ALARM_OVERTEMP and dropping power to 0 kW.
    generation_records = []
    telemetry_records = []

    for ts in timestamps:
        hour = ts.hour
        day_idx = (ts.date() - start_date).days
        w_item = weather_obs[timestamps.index(ts)]
        ghi = w_item["ghi_wm2"]
        amb_t = w_item["ambient_temp_c"]

        # Base power per healthy inverter (kW)
        if ghi > 10.0:
            healthy_inv_kw = round((ghi / 1000.0) * inverter_capacity_kw * 0.86 * (1.0 - 0.004 * max(0.0, amb_t - 25.0)), 1)
            healthy_inv_kw = min(healthy_inv_kw, inverter_capacity_kw)
        else:
            healthy_inv_kw = 0.0

        hourly_plant_mw = 0.0

        # Grid curtailment on Day 3 (13:00 to 15:00): plant capped at 30 MW
        curtailment_active = (day_idx == 3 and 13 <= hour <= 14)

        for inv_i in range(1, num_inverters + 1):
            inv_id = f"INV-{inv_i:02d}"
            is_inv4 = (inv_i == 4)
            is_inv4_tripped = is_inv4 and (day_idx in [2, 3, 4, 5]) and (11 <= hour <= 13)

            if is_inv4_tripped:
                # Tripped state
                inv_kw = 0.0
                inv_temp = round(71.5 + (hour - 11) * 1.5 + random.uniform(0.1, 1.2), 1)
                op_state = "fault_trip"
                alarm_code = "INV_ALARM_OVERTEMP"
                alarm_desc = "IGBT module heatsink overtemperature threshold (>70C) exceeded"
                dc_v = 845.0
                dc_i = 0.0
            else:
                inv_kw = healthy_inv_kw
                inv_temp = round(amb_t + (inv_kw / 5000.0) * 24.0 + random.uniform(-1.0, 1.0), 1)
                op_state = "running" if inv_kw > 0 else "standby"
                alarm_code = None
                alarm_desc = None
                dc_v = round(830.0 + random.uniform(-5.0, 5.0), 1) if inv_kw > 0 else 0.0
                dc_i = round(inv_kw / (dc_v * 0.985 / 1000.0), 1) if dc_v > 0 and inv_kw > 0 else 0.0

            # Scale if curtailment is active across all inverters
            if curtailment_active and inv_kw > 0:
                inv_kw = min(inv_kw, 3000.0)  # Capped at 3 MW each = 30 MW total

            inv_mw = round(inv_kw / 1000.0, 3)
            hourly_plant_mw += inv_mw

            telemetry_records.append({
                "timestamp": ts.isoformat(),
                "asset_id": inv_id,
                "ac_power_kw": inv_kw,
                "dc_power_kw": round(inv_kw / 0.982, 1) if inv_kw > 0 else 0.0,
                "dc_voltage_v": dc_v,
                "dc_current_a": dc_i,
                "inverter_temp_c": inv_temp,
                "efficiency_pct": 98.2 if inv_kw > 0 else 0.0,
                "operating_state": op_state,
                "alarm_code": alarm_code,
                "alarm_description": alarm_desc,
                "source_file": "equipment_telemetry.csv",
                "source_row_index": len(telemetry_records) + 1
            })

            generation_records.append({
                "timestamp": ts.isoformat(),
                "plant_id": plant_id,
                "asset_id": inv_id,
                "actual_mw": inv_mw,
                "actual_mwh": inv_mw,
                "source_file": "generation_helios50.csv",
                "source_row_index": len(generation_records) + 1
            })

        # Also add plant-level total record (asset_id = None)
        generation_records.append({
            "timestamp": ts.isoformat(),
            "plant_id": plant_id,
            "asset_id": None,
            "actual_mw": round(hourly_plant_mw, 2),
            "actual_mwh": round(hourly_plant_mw, 2),
            "source_file": "generation_helios50.csv",
            "source_row_index": len(generation_records) + 1
        })

    # --- 3. External Events (Grid Curtailment) ---
    external_events = [
        {
            "plant_id": plant_id,
            "timestamp_start": (datetime.combine(start_date + timedelta(days=3), datetime.min.time()) + timedelta(hours=13)).isoformat(),
            "timestamp_end": (datetime.combine(start_date + timedelta(days=3), datetime.min.time()) + timedelta(hours=15)).isoformat(),
            "event_type": "grid_curtailment",
            "curtailed_capacity_mw": 15.0,
            "iso_directive_code": "CAISO-DIR-9921",
            "compensation_eligible": "YES",
            "impact_description": "Regional transmission congestion constraint in Southern California corridor",
            "source_file": "external_events.csv",
            "source_row_index": 1
        }
    ]

    # --- 4. Workforce Records ---
    workforce_records = []
    for d in range(num_days):
        day_date = start_date + timedelta(days=d)
        for shift in ["morning", "afternoon", "night"]:
            techs = 3 if shift == "morning" else (2 if shift == "afternoon" else 1)
            workforce_records.append({
                "plant_id": plant_id,
                "date": day_date.strftime("%Y-%m-%d"),
                "shift": shift,
                "technicians_on_site": techs,
                "hours_logged": 8.0,
                "lead_technician": "Carlos Mendez" if shift == "morning" else "Sarah Jenkins",
                "technician_roster": "C. Mendez, J. Doe, A. Patel" if techs == 3 else "S. Jenkins, R. Vance",
                "skill_certifications": "HV_Certified, Inverter_Specialist, OSHA_10",
                "notes": "Routine inspection and thermal checks completed",
                "source_file": "workforce_shifts.csv",
                "source_row_index": len(workforce_records) + 1
            })

    # --- 5. Maintenance Records ---
    maintenance_records = [
        {
            "plant_id": plant_id,
            "work_order_id": "WO-2026-INV04",
            "asset_id": "INV-04",
            "maintenance_type": "corrective",
            "scheduled_start": (datetime.combine(start_date + timedelta(days=4), datetime.min.time()) + timedelta(hours=14)).isoformat(),
            "scheduled_end": (datetime.combine(start_date + timedelta(days=4), datetime.min.time()) + timedelta(hours=16)).isoformat(),
            "actual_start": (datetime.combine(start_date + timedelta(days=4), datetime.min.time()) + timedelta(hours=14, minutes=15)).isoformat(),
            "actual_end": (datetime.combine(start_date + timedelta(days=4), datetime.min.time()) + timedelta(hours=16)).isoformat(),
            "downtime_hours": 1.75,
            "technician_in_charge": "Carlos Mendez",
            "procedure_code": "SOP-INV-02",
            "procedure_description": "Inverter heatsink filter clean and thermal compound re-application",
            "status": "in_progress",
            "source_file": "maintenance_records.csv",
            "source_row_index": 1
        },
        {
            "plant_id": plant_id,
            "work_order_id": "WO-2026-PM01",
            "asset_id": "TX-01",
            "maintenance_type": "preventative",
            "scheduled_start": (datetime.combine(start_date + timedelta(days=1), datetime.min.time()) + timedelta(hours=2)).isoformat(),
            "scheduled_end": (datetime.combine(start_date + timedelta(days=1), datetime.min.time()) + timedelta(hours=4)).isoformat(),
            "actual_start": (datetime.combine(start_date + timedelta(days=1), datetime.min.time()) + timedelta(hours=2)).isoformat(),
            "actual_end": (datetime.combine(start_date + timedelta(days=1), datetime.min.time()) + timedelta(hours=3, minutes=45)).isoformat(),
            "downtime_hours": 0.0,  # Scheduled during night, zero generation impact
            "technician_in_charge": "Sarah Jenkins",
            "procedure_code": "SOP-TX-01",
            "procedure_description": "Dissolved gas analysis (DGA) and oil sampling on main step-up transformer",
            "status": "completed",
            "source_file": "maintenance_records.csv",
            "source_row_index": 2
        }
    ]

    # --- 6. Financial Assumptions ---
    financial_records = [
        {
            "plant_id": plant_id,
            "effective_date": start_date.strftime("%Y-%m-%d"),
            "ppa_tariff_usd_per_mwh": 48.50,
            "om_hourly_cost_usd": 125.00,
            "curtailment_compensation_usd_per_mwh": 40.00,
            "budgeted_monthly_generation_mwh": 8500.0,
            "budgeted_monthly_revenue_usd": 412250.0,
            "budgeted_monthly_opex_usd": 38000.0,
            "source_file": "financial_assumptions.csv",
            "source_row_index": 1
        }
    ]

    # --- 7. Malformed / Quarantine Test Dataset ---
    # Deliberately malformed records to verify ingestion validation and quarantine
    malformed_records = [
        {"timestamp": "INVALID_DATE_FORMAT", "plant_id": plant_id, "actual_mw": 25.0, "actual_mwh": 25.0, "asset_id": "INV-01"},
        {"timestamp": (datetime.combine(start_date, datetime.min.time()) + timedelta(hours=10)).isoformat(), "plant_id": plant_id, "actual_mw": -99.0, "actual_mwh": -99.0, "asset_id": "INV-02"},  # Negative power
        {"timestamp": (datetime.combine(start_date, datetime.min.time()) + timedelta(hours=11)).isoformat(), "plant_id": plant_id, "actual_mw": "CORRUPTED_TEXT", "actual_mwh": None, "asset_id": "INV-03"},
        {"timestamp": (datetime.combine(start_date, datetime.min.time()) + timedelta(hours=12)).isoformat(), "plant_id": plant_id, "actual_mw": 4.5, "actual_mwh": 4.5, "asset_id": "NON_EXISTENT_ASSET_999"},
        {"timestamp": None, "plant_id": plant_id, "actual_mw": 12.0, "actual_mwh": 12.0, "asset_id": "INV-05"}
    ]

    # Save to CSV files
    pd.DataFrame(generation_records).to_csv(os.path.join(output_dir, "generation_helios50.csv"), index=False)
    pd.DataFrame(forecast_da).to_csv(os.path.join(output_dir, "forecast_day_ahead.csv"), index=False)
    pd.DataFrame(forecast_ma).to_csv(os.path.join(output_dir, "forecast_month_ahead.csv"), index=False)
    pd.DataFrame(telemetry_records).to_csv(os.path.join(output_dir, "equipment_telemetry.csv"), index=False)
    pd.DataFrame(weather_obs).to_csv(os.path.join(output_dir, "weather_observations.csv"), index=False)
    pd.DataFrame(external_events).to_csv(os.path.join(output_dir, "external_events.csv"), index=False)
    pd.DataFrame(workforce_records).to_csv(os.path.join(output_dir, "workforce_shifts.csv"), index=False)
    pd.DataFrame(maintenance_records).to_csv(os.path.join(output_dir, "maintenance_records.csv"), index=False)
    pd.DataFrame(financial_records).to_csv(os.path.join(output_dir, "financial_assumptions.csv"), index=False)
    pd.DataFrame(malformed_records).to_csv(os.path.join(output_dir, "malformed_test_samples.csv"), index=False)

    print(f"Generated synthetic 50 MW plant datasets in: {output_dir}")
    print(f"  - Generation records: {len(generation_records)}")
    print(f"  - Forecast records (DA): {len(forecast_da)}")
    print(f"  - Equipment telemetry records: {len(telemetry_records)}")
    print(f"  - Weather records: {len(weather_obs)}")
    print(f"  - Malformed test records: {len(malformed_records)}")

if __name__ == "__main__":
    generate_synthetic_plant_data()
