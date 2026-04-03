import sqlite3
from datetime import datetime
from config import Config
from database.database import get_db_connection

class AttendanceCalculator:
    """
    Handles the calculation of subject-wise attendance from session-level data.
    Maps P1-P7 periods to subjects using the timetable and updates cumulative records.
    """
    
    @staticmethod
    def get_subject_for_period(day_name, period_num):
        """Fetches the subject code for a given day and period number."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject_code FROM timetable WHERE day = ? AND period = ?", (day_name.upper(), period_num))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    @staticmethod
    def is_session_calculated(session_type, date_str):
        """Checks if a session has already been calculated for a given date."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_calculated FROM session_calculation_status WHERE date = ? AND session_type = ?", (date_str, session_type))
        result = cursor.fetchone()
        conn.close()
        return result[0] == 1 if result else False

    @staticmethod
    def mark_session_calculated(session_type, date_str):
        """Marks a session as calculated in the status table."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO session_calculation_status (date, session_type, is_calculated) VALUES (?, ?, 1)", (date_str, session_type))
        conn.commit()
        conn.close()

    @staticmethod
    def process_session(session_type, date_str):
        """
        Main workflow to translate periodic session attendance to cumulative subject attendance.
        """
        # 1. Sequential Safeguard: Morning must be calculated before Afternoon
        if session_type == "Afternoon":
            if not AttendanceCalculator.is_session_calculated("Morning", date_str):
                return {"success": False, "message": "Morning session must be calculated before Afternoon."}
        
        # 2. Check for duplicate calculation
        if AttendanceCalculator.is_session_calculated(session_type, date_str):
            return {"success": False, "message": f"{session_type} session for {date_str} has already been calculated."}

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine day of week
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = dt.strftime('%A').upper()
        
        # Determine target table and periods
        active_table = "morning_attendance" if session_type == "Morning" else "afternoon_attendance"
        periods = ['P1', 'P2', 'P3', 'P4'] if session_type == "Morning" else ['P5', 'P6', 'P7']
        
        # 3. Fetch session data
        cursor.execute(f"SELECT * FROM {active_table} WHERE date = ?", (date_str,))
        session_rows = cursor.fetchall()
        
        # Get column names to handle indices
        cursor.execute(f"PRAGMA table_info({active_table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if not session_rows:
            return {"success": False, "message": f"No records found in {active_table} for {date_str}."}

        try:
            cursor.execute("BEGIN TRANSACTION")
            
            for row in session_rows:
                student_id = row[columns.index('student_id')]
                
                for p_col in periods:
                    status = row[columns.index(p_col)]
                    p_num = int(p_col[1]) # Extract 1 from 'p1'
                    
                    # Map to subject
                    subject_code = AttendanceCalculator.get_subject_for_period(day_name, p_num)
                    
                    if not subject_code:
                        # Skip periods without a defined subject (labs/placements)
                        continue
                        
                    # Update Main Cumulative Attendance
                    if status == 'P':
                        cursor.execute('''
                            UPDATE main_attendance 
                            SET present_count = present_count + 1, total_count = total_count + 1
                            WHERE student_id = ? AND subject_code = ?
                        ''', (student_id, subject_code))
                    elif status == 'DL':
                        cursor.execute('''
                            UPDATE main_attendance 
                            SET duty_leave_count = duty_leave_count + 1, total_count = total_count + 1
                            WHERE student_id = ? AND subject_code = ?
                        ''', (student_id, subject_code))
                    elif status == 'A':
                        cursor.execute('''
                            UPDATE main_attendance 
                            SET total_count = total_count + 1
                            WHERE student_id = ? AND subject_code = ?
                        ''', (student_id, subject_code))
                    
                    # Archive to History
                    cursor.execute('''
                        INSERT INTO history_attendance (date, student_id, period, status_code)
                        VALUES (?, ?, ?, ?)
                    ''', (date_str, student_id, p_col.upper(), status))

            # 4. Clear Active Session Data after processing
            cursor.execute(f"DELETE FROM {active_table} WHERE date = ?", (date_str,))
            
            # 5. Mark as Calculated
            cursor.execute("INSERT OR REPLACE INTO session_calculation_status (date, session_type, is_calculated) VALUES (?, ?, 1)", (date_str, session_type))
            
            conn.commit()
            return {"success": True, "message": f"{session_type} session attendance calculated and archived successfully."}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": f"Calculation error: {str(e)}"}
        finally:
            conn.close()
