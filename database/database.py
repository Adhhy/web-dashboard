import sqlite3
import os
from config import Config

DB_NAME = str(Config.AUTH_DB_PATH)

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def init_session(session_type):
    """
    Initialize the attendance table for the current day.
    Pre-populates with all students in the database markers if they don't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_date = os.popen('date /t').read().strip() # Simple date string or use datetime
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    table_name = "morning_attendance" if session_type == "Morning" else "afternoon_attendance"
    
    # Fetch all students (from advisors/users or a dedicated students table if existed)
    # For now, we'll initialize logs for students who have sent logs or exist in advisor batches.
    # A better way is to have a students table. Assuming we just initialize for found students.
    
    cursor.execute(f"SELECT DISTINCT student_id FROM policy_logs WHERE date = ?", (current_date,))
    students = cursor.fetchall()
    
    for (student_id,) in students:
        try:
            cursor.execute(f"INSERT OR IGNORE INTO {table_name} (student_id, date) VALUES (?, ?)", (student_id, current_date))
        except sqlite3.OperationalError:
            pass # Table might not be ready
            
    conn.commit()
    conn.close()

def update_session_attendance(student_id, period, status, session_type):
    """
    Update the status of a specific period for a student.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    table_name = "morning_attendance" if session_type == "Morning" else "afternoon_attendance"
    
    try:
        cursor.execute(f"UPDATE {table_name} SET {period} = ? WHERE student_id = ? AND date = ?", (status, student_id, current_date))
        conn.commit()
    except Exception as e:
        print(f"Error updating attendance: {e}")
    finally:
        conn.close()

def is_session_finalized(session_type, date):
    """
    Check if a session (Morning/Afternoon) for a given date has already been processed.
    Returns True if records exist in the corresponding attendance table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "morning_attendance" if session_type == "Morning" else "afternoon_attendance"
    
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE date = ?", (date,))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"Error checking session status: {e}")
        return False
    finally:
        conn.close()

def clear_session_logs(session_type, date):
    """
    Clear only the logs for the specific session and date that were finalized.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM policy_logs WHERE session_type = ? AND date = ?", (session_type, date))
        conn.commit()
    except Exception as e:
        print(f"Error clearing logs: {e}")
    finally:
        conn.close()

