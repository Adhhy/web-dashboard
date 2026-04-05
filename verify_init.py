import sqlite3
import os
import sys

# Add project root for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def verify_db():
    db_path = Config.AUTH_DB_PATH
    if not os.path.exists(db_path):
        print(f"Error: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'users', 'students', 'advisors', 'teachers', 'teacher_subjects',
        'subjects', 'timetable', 'main_attendance', 'session_calculation_status',
        'history_attendance', 'policy_logs', 'morning_attendance', 'afternoon_attendance',
        'device_requests', 'devices', 'sessions', 'device_commands', 'duty_leave_requests'
    ]
    
    print(f"Found {len(tables)} tables.")
    missing = [t for t in expected_tables if t not in tables]
    
    if missing:
        print(f"Missing tables: {missing}")
    else:
        print("All 18 expected tables are present.")
        
    conn.close()

if __name__ == '__main__':
    verify_db()
