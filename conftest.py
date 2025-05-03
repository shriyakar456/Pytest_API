import sqlite3
from datetime import datetime

def pytest_runtest_logreport(report):
    if report.when == 'call':
        conn = sqlite3.connect("test_reports.db",check_same_thread=False)
        cursor = conn.cursor()
        status = "PASS" if report.passed else "FAIL"
        cursor.execute("INSERT INTO test_results (test_name, status, timestamp) VALUES (?, ?, ?)",
                       (report.nodeid, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
