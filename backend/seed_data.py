import os
from datetime import datetime, date, timedelta
from app.database import engine, Base, SessionLocal
from app.ingestion.pipeline import IngestionPipeline
from app.models.investigation import Investigation
from app.models.work_order import WorkOrder
from sample_data.generator import generate_synthetic_plant_data

def seed_database():
    print("Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        pipeline = IngestionPipeline(db)
        plant = pipeline.ensure_default_plant_and_assets("helios-50")
        print(f"Ensured plant: {plant.name}")

        sample_dir = "D:/Globathon/backend/sample_data"
        if not os.path.exists(os.path.join(sample_dir, "generation_helios50.csv")):
            print("Generating synthetic datasets...")
            generate_synthetic_plant_data(output_dir=sample_dir)

        # Ingestion order:
        datasets = [
            ("financial_assumptions.csv", "financial"),
            ("forecast_day_ahead.csv", "forecast"),
            ("forecast_month_ahead.csv", "forecast"),
            ("generation_helios50.csv", "generation"),
            ("equipment_telemetry.csv", "equipment"),
            ("weather_observations.csv", "weather"),
            ("external_events.csv", "external_events"),
            ("workforce_shifts.csv", "workforce"),
            ("maintenance_records.csv", "maintenance"),
        ]

        for fname, ftype in datasets:
            fpath = os.path.join(sample_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                report = pipeline.ingest_csv(
                    file_content=content,
                    filename=fname,
                    file_type=ftype,
                    plant_id="helios-50"
                )
                print(f"Ingested {fname} ({ftype}): {report.valid_records} valid, {report.quarantined_records} quarantined.")

        # Seed initial Investigation
        existing_inv = db.query(Investigation).filter(Investigation.cause_id == "CAUSE-INV-04-THERMAL-TRIP").first()
        if not existing_inv:
            inv = Investigation(
                plant_id="helios-50",
                cause_id="CAUSE-INV-04-THERMAL-TRIP",
                title="Investigation: Inverter INV-04 Midday Thermal Trip Recurrence",
                cause_category="equipment_fault",
                description="Inverter #04 repeatedly exceeded 70C IGBT threshold between 11:00 and 13:00 over 4 consecutive operational days. Preliminary inspection indicates dust clogging of cabinet air intake filters.",
                owner="Carlos Mendez (Operations Lead)",
                status="in_progress",
                priority="critical",
                controllability="controllable",
                recurrence_flag=True,
                deadline=datetime.utcnow() + timedelta(days=2),
                action_plan="1. Apply LOTO isolation.\n2. Disassemble and replace intake filter elements.\n3. Verify cooling fan tachometer signals and replace worn capacitor.\n4. Re-commission and thermal test."
            )
            db.add(inv)

        # Seed initial Work Order
        existing_wo = db.query(WorkOrder).filter(WorkOrder.work_order_number == "WO-2026-INV04").first()
        if not existing_wo:
            wo = WorkOrder(
                work_order_number="WO-2026-INV04",
                plant_id="helios-50",
                asset_id="INV-04",
                title="Emergency Inspection & Heat Exchanger Servicing - INV-04",
                description="Inspect cooling fan blower motors, replace intake air filters (Part #FIL-SMA-004), and check IGBT thermal interface compound integrity.",
                priority="P1_CRITICAL",
                status="in_progress",
                assigned_technician="Carlos Mendez",
                estimated_hours=3.5,
                procedure_code="SOP-INV-02",
                safety_interlock_verified=True,
                loto_applied=True
            )
            db.add(wo)

        db.commit()
        print("Database seeded successfully with realistic plant performance dataset!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
