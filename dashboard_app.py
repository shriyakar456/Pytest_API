from flask import Flask, render_template, request
import sqlite3, os
from dotenv import load_dotenv

load_dotenv()  # ✅ Load environment variables

app = Flask(__name__)
REPORT_DB_PATH = os.getenv("REPORT_DB", "test_reports.db")

def init_report_db():
    if not os.path.exists(REPORT_DB_PATH):
        conn = sqlite3.connect(REPORT_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS test_results (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, timestamp TEXT, test_name TEXT, status TEXT )")
        conn.commit()
        conn.close()

@app.route("/")
def dashboard():
    try:
        conn = sqlite3.connect(REPORT_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        status_filter = request.args.get("status")
        if status_filter:
            cursor.execute("SELECT * FROM test_results WHERE status=? ORDER BY timestamp DESC", (status_filter,))
        else:
            cursor.execute("SELECT * FROM test_results ORDER BY timestamp DESC")
        results = cursor.fetchall()

        cursor.execute("SELECT run_id FROM test_results ORDER BY timestamp DESC LIMIT 1")
        latest_run = cursor.fetchone()

        summary = {"timestamp": "N/A", "PASS": 0, "FAIL": 0}
        if latest_run:
            latest_run_id = latest_run[0]
            cursor.execute("SELECT timestamp FROM test_results WHERE run_id=? LIMIT 1", (latest_run_id,))
            ts_row = cursor.fetchone()
            summary["timestamp"] = ts_row[0] if ts_row else "N/A"

            cursor.execute("SELECT status, COUNT(*) FROM test_results WHERE run_id=? GROUP BY status", (latest_run_id,))
            counts = cursor.fetchall()
            for status, count in counts:
                summary[status] = count

        conn.close()
        summary["PASS"] = summary.get("PASS", 0)
        summary["FAIL"] = summary.get("FAIL", 0)
        return render_template("dashboard.html", results=results, summary=summary)

    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"

init_report_db()
