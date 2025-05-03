import subprocess
import time
import os
import webbrowser
import pytest
import sqlite3
import requests
from pathlib import Path

import shutil

# Create a temporary DB copy
shutil.copy("users.db", "temp_users.db")
os.environ["USER_DB"] = "temp_users.db"

# === Paths and Constants ===
ROOT = Path(__file__).parent.resolve()
API_SCRIPT = "app_login.py"
DASHBOARD_SCRIPT = "dashboard_app.py"
DASHBOARD_URL = "http://127.0.0.1:5000"
REPORT_DB = ROOT / "test_reports.db"

# === Create test_reports.db if missing ===
def ensure_report_db():
    if not REPORT_DB.exists():
        print("🛠️ Creating test_reports.db...")
        conn = sqlite3.connect(REPORT_DB,check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                status TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
    else:
        print("✅ test_reports.db exists")

# === Start Flask API ===
def start_api():
    print("🚀 Starting Flask API...")
    return subprocess.Popen(["python", API_SCRIPT], cwd=ROOT)

# === Run Pytest Tests ===
def run_tests():
    print("🧪 Running tests...")
    pytest.main(["."])

# === Start Dashboard and wait until it's ready ===
def start_dashboard():
    print("📊 Launching Dashboard Server...")
    subprocess.Popen(["python", DASHBOARD_SCRIPT], cwd=ROOT)

    max_wait = 15
    for i in range(max_wait):
        try:
            r = requests.get(DASHBOARD_URL)
            if r.status_code == 200:
                print("✅ Dashboard is live!")
                break
            else:
                print(f"⚠️ Received status {r.status_code}, retrying... ({i+1}s)")
        except requests.exceptions.ConnectionError:
            print(f"⏳ Waiting for dashboard... ({i+1}s)")
        time.sleep(1)
    else:
        print("⚠️ Dashboard didn't start in time.")

    webbrowser.open(DASHBOARD_URL)
    
def clear_old_test_data():
    conn = sqlite3.connect(REPORT_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_results")
    conn.commit()
    conn.close()
    print("🧹 Cleared old test results")

# === Orchestrator ===
def main():
    ensure_report_db()
    api_proc = start_api()
    time.sleep(3)  # let Flask boot

    try:
        clear_old_test_data()
        run_tests()
        print("⏳ Waiting for DB write flush...")
        time.sleep(2)
        start_dashboard()
        print("✅ All systems running! Dashboard launched.")
    finally:
        print("🛑 Stopping Flask API...")
        try:
            api_proc.terminate()
            api_proc.wait(timeout=5)
            print("✅ API shut down successfully.")
        except Exception as e:
            print("⚠️ Error stopping API:", e)
            api_proc.kill()

if __name__ == "__main__":
    main()
