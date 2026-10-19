import os
import sys
import subprocess
import time

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    print("===================================================================")
    print("AI-Powered Plant Performance Intelligence System (Helios-50)")
    print("===================================================================")

    # 1. Seed database if not already present
    db_path = os.path.join(backend_dir, "plant_data.db")
    if not os.path.exists(db_path):
        print("\n[1/3] Seeding SQLite database with synthetic 50 MW plant data...")
        subprocess.run([sys.executable, "seed_data.py"], cwd=backend_dir, check=True)
    else:
        print("\n[1/3] Database found: plant_data.db is ready.")

    # 2. Start Backend with Uvicorn
    print("\n[2/3] Starting FastAPI Backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=backend_dir
    )

    # 3. Start Frontend with Vite
    print("\n[3/3] Starting Vite Frontend on http://localhost:5173...")
    shell_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        shell_cmd,
        cwd=frontend_dir,
        shell=True
    )

    print("\n===================================================================")
    print("System Running!")
    print(" - Frontend UI:    http://localhost:5173")
    print(" - Backend API:   http://127.0.0.1:8000")
    print(" - API Swagger:   http://127.0.0.1:8000/docs")
    print("===================================================================")
    print("Press Ctrl+C to terminate both servers.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Services stopped.")

if __name__ == "__main__":
    main()
