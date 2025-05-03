from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

def init_report_db():
    if not os.path.exists("test_reports.db"):
        conn = sqlite3.connect("test_reports.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                status TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

@app.route("/")
def dashboard():
    print("🟢 / route hit")
    try:
        conn = sqlite3.connect("test_reports.db", check_same_thread=False)
        cursor = conn.cursor()

        status_filter = request.args.get("status")
        if status_filter:
            print(f"🔍 Filtering by status: {status_filter}")
            cursor.execute("SELECT * FROM test_results WHERE status=? ORDER BY timestamp DESC", (status_filter,))
        else:
            cursor.execute("SELECT * FROM test_results ORDER BY timestamp DESC")
        results = cursor.fetchall()

        cursor.execute("SELECT timestamp FROM test_results ORDER BY timestamp DESC LIMIT 1")
        latest_time_row = cursor.fetchone()

        summary = {"timestamp": "N/A", "PASS": 0, "FAIL": 0}
        if latest_time_row:
            latest_time = latest_time_row[0]
            summary["timestamp"] = latest_time

            cursor.execute("""
                SELECT status, COUNT(*)
                FROM test_results
                WHERE timestamp=?
                GROUP BY status
            """, (latest_time,))

            result_counts = cursor.fetchall()
            for status, count in result_counts:
                summary[status] = count

        summary["PASS"] = summary.get("PASS", 0)
        summary["FAIL"] = summary.get("FAIL", 0)
        conn.close()

        print(f"📊 {len(results)} results loaded from DB")
        return render_template("dashboard.html", results=results, summary=summary)

    except Exception as e:
        print("❌ Error while loading dashboard:", e)
        return f"<h1>Error</h1><p>{e}</p>"

# Initialize DB only if running locally
init_report_db()
