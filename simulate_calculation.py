import sqlite3
import os
import sys
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import Config
from database.database import get_db_connection
from attendance.calculator import AttendanceCalculator

def simulate():
    db_path = Config.AUTH_DB_PATH
    test_date = '2026-04-03' # Friday
    student_id = 'Adithyan'
    
    print(f"--- Simulating Attendance Calculation for {student_id} on {test_date} (Friday) ---")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Setup Mock Data
    print("Setting up mock session data...")
    
    # Reset counts in main_attendance for a clean test
    cursor.execute("UPDATE main_attendance SET present_count = 0, duty_leave_count = 0, total_count = 0 WHERE student_id = ?", (student_id,))
    
    # Morning: P1=P(CGIP), P2=A(NULL), P3=DL(NULL), P4=P(NULL)
    cursor.execute("DELETE FROM morning_attendance WHERE date = ?", (test_date,))
    cursor.execute('''
        INSERT INTO morning_attendance (student_id, date, p1, p2, p3, p4)
        VALUES (?, ?, 'P', 'A', 'DL', 'P')
    ''', (student_id, test_date))
    
    # Afternoon: P5=P(NULL), P6=A(CGIP), P7=P(PE)
    cursor.execute("DELETE FROM afternoon_attendance WHERE date = ?", (test_date,))
    cursor.execute('''
        INSERT INTO afternoon_attendance (student_id, date, p5, p6, p7)
        VALUES (?, ?, 'P', 'A', 'P')
    ''', (student_id, test_date))
    
    # Clear status for fresh test
    cursor.execute("DELETE FROM session_calculation_status WHERE date = ?", (test_date,))
    
    # Clear history for this test date
    cursor.execute("DELETE FROM history_attendance WHERE date = ?", (test_date,))
    
    conn.commit()
    
    # 2. Process Morning
    print("Processing Morning Session...")
    res_m = AttendanceCalculator.process_session("Morning", test_date)
    print(f"Morning Result: {res_m}")
    
    # 3. Process Afternoon
    print("Processing Afternoon Session...")
    res_a = AttendanceCalculator.process_session("Afternoon", test_date)
    print(f"Afternoon Result: {res_a}")
    
    # 4. Verify Main Attendance
    print("\n--- Verification: Main Attendance ---")
    cursor.execute("SELECT * FROM main_attendance WHERE student_id = ?", (student_id,))
    main_res = cursor.fetchall()
    
    found_any = False
    for row in main_res:
        if row[4] > 0: 
            found_any = True
            print(f"Subject: {row[1]} | Present: {row[2]} | DL: {row[3]} | Total: {row[4]}")
            
    if not found_any:
        print("No subjects found with > 0 total_count.")
        
    # 5. Verify History
    print("\n--- Verification: History ---")
    cursor.execute("SELECT * FROM history_attendance WHERE date = ?", (test_date,))
    hist_res = cursor.fetchall()
    print(f"Total history entries: {len(hist_res)}")
    for row in hist_res:
        print(f"Date: {row[1]} | Period: {row[3]} | Status: {row[4]}")

    conn.close()

if __name__ == '__main__':
    simulate()
