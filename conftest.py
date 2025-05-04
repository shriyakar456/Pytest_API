import sqlite3
from datetime import datetime
import uuid

# Static run_id and timestamp for the entire session
RUN_ID = str(uuid.uuid4())
RUN_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def pytest_sessionstart(session):
    conn = sqlite3.connect("test_reports.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS test_results (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, timestamp TEXT, test_name TEXT, status TEXT )")
    cursor.execute("DELETE FROM test_results WHERE run_id=?", (RUN_ID,))
    conn.commit()
    conn.close()

def pytest_runtest_logreport(report):
    if report.when == 'call':
        conn = sqlite3.connect("test_reports.db", check_same_thread=False)
        cursor = conn.cursor()
        status = "PASS" if report.passed else "FAIL"
        cursor.execute("INSERT INTO test_results (run_id, timestamp, test_name, status) VALUES (?, ?, ?, ?) ", (RUN_ID, RUN_TIMESTAMP, report.nodeid, status))
        conn.commit()
        conn.close()
