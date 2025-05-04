from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

def init_report_db():
    if not os.path.exists("test_reports.db"):
        conn = sqlite3.connect("test_reports.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS test_results (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, timestamp TEXT, test_name TEXT, status TEXT ) ")
        conn.commit()
        conn.close()

@app.route("/")
def dashboard():
    try:
        conn = sqlite3.connect("test_reports.db", check_same_thread=False)
        cursor = conn.cursor()

        status_filter = request.args.get("status")

        # Get latest run_id by timestamp
        cursor.execute("SELECT run_id, MAX(timestamp) FROM test_results")
        row = cursor.fetchone()
        if not row or not row[0]:
            return "<h1>No test results found</h1>"

        run_id = row[0]

        if status_filter:
            cursor.execute("SELECT test_name, status, timestamp FROM test_results WHERE run_id=? AND status=? ORDER BY id DESC", (run_id, status_filter))
        else:
            cursor.execute("SELECT test_name, status, timestamp FROM test_results WHERE run_id=? ORDER BY id DESC", (run_id,))
        results = cursor.fetchall()

        # Get summary
        cursor.execute("""
            SELECT status, COUNT(*) FROM test_results
            WHERE run_id=?
            GROUP BY status
        """, (run_id,))
        summary_data = cursor.fetchall()
        summary = {"timestamp": row[1], "PASS": 0, "FAIL": 0}
        for status, count in summary_data:
            summary[status] = count

        conn.close()
        return render_template("dashboard.html", results=results, summary=summary)

    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"

init_report_db()
