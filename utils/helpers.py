import sqlite3
import os
import sys

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def get_advisor_details(user_id):
    """
    Fetch advisor details using JOIN between users and advisors.
    Returns a dictionary with name, department, batch, role.
    """
    db_path = Config.AUTH_DB_PATH
    
    if not os.path.exists(db_path):
        return None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.name, a.department, a.batch, u.role
            FROM advisors a
            JOIN users u ON a.user_id = u.id
            WHERE u.id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            "name": row[0],
            "department": row[1],
            "batch": row[2],
            "role": row[3]
        }
    except Exception as e:
        print(f"Error fetching advisor details: {e}")
        return None

from datetime import datetime

def is_advisor(user_id):
    """Check if a user has the advisor role."""
    details = get_advisor_details(user_id)
    return details is not None and details.get('role') == 'advisor'

def get_active_device():
    """
    Fetch the active device and its connection status.
    Returns a dictionary with name and status.
    """
    db_path = Config.AUTH_DB_PATH
    
    if not os.path.exists(db_path):
        return {"name": "Not Available", "status": "Disconnected", "device_id": None}
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch the first active device (most recently approved/seen)
        cursor.execute("""
            SELECT device_id, device_name, connection_status 
            FROM devices 
            ORDER BY last_seen DESC 
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return {"name": "Not Available", "status": "Disconnected", "device_id": None}

        # Map status: "connected" -> "Connected", others -> "Disconnected"
        status = "Connected" if row[2] == "connected" else "Disconnected"

        return {
            "device_id": row[0],
            "name": row[1],
            "status": status
        }
    except Exception as e:
        print(f"Error fetching active device: {e}")
        return {"name": "Not Available", "status": "Disconnected", "device_id": None}

def get_session_info():
    """Fetch current session status and timestamps."""
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status, started_at, stopped_at FROM sessions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "status": row[0],
                "started_at": row[1],
                "stopped_at": row[2]
            }
        return {"status": "idle", "started_at": None, "stopped_at": None}
    except Exception as e:
        print(f"Error fetching session info: {e}")
        return {"status": "idle", "started_at": None, "stopped_at": None}

def update_session_state(new_status):
    """
    Update session status and dispatch corresponding device command.
    status: active, stopped, idle
    """
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Determine command based on session status
        command = "idle"
        if new_status == "active":
            command = "start_camera"
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE sessions 
                SET status = 'active', started_at = ?, stopped_at = NULL 
                WHERE id = (SELECT id FROM sessions ORDER BY id DESC LIMIT 1)
            """, (start_time,))
        elif new_status == "stopped":
            command = "stop_camera"
            stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # We move to 'idle' status globally but track the stop_time for history
            # This ensures that on refresh, the session is IDLE and ready to start again.
            cursor.execute("""
                UPDATE sessions 
                SET status = 'idle', stopped_at = ? 
                WHERE id = (SELECT id FROM sessions ORDER BY id DESC LIMIT 1)
            """, (stop_time,))
        else:
            cursor.execute("""
                UPDATE sessions 
                SET status = 'idle' 
                WHERE id = (SELECT id FROM sessions ORDER BY id DESC LIMIT 1)
            """)

        # Dispatch command to the active device
        active_device = get_active_device()
        if active_device["device_id"]:
            # We explicitly update the command for the device.
            # If we just stopped, the device will receive 'stop_camera' once, then it will poll 'idle' later?
            # Actually, let's keep the command as stop_camera until the user starts again?
            # Or better, let's keep it as the last instruction.
            cursor.execute("""
                INSERT INTO device_commands (device_id, command, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(device_id) DO UPDATE SET command = excluded.command, updated_at = CURRENT_TIMESTAMP
            """, (active_device["device_id"], command))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating session state: {e}")
        return False

def get_device_command(device_id):
    """Fetch the current command for a specific device."""
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT command, updated_at FROM device_commands WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"command": row[0], "updated_at": row[1]}
        return {"command": "idle", "updated_at": None}
    except Exception as e:
        print(f"Error fetching device command: {e}")
        return {"command": "idle", "updated_at": None}

def get_student_details(user_id):
    """Fetch student profile information."""
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, student_id, ktu_id, department, batch 
            FROM students WHERE user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "name": row[0],
                "student_id": row[1],
                "ktu_id": row[2] if row[2] else "N/A",
                "department": row[3],
                "batch": row[4]
            }
        return None
    except Exception as e:
        print(f"Error fetching student details: {e}")
        return None

def get_student_attendance(student_id):
    """Fetch cumulative subject-wise attendance for a student."""
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Ensure we sort subjects so they always appear in consistent order
        cursor.execute('''
            SELECT m.subject_code, m.present_count, m.duty_leave_count, m.total_count,
                   s.full_name, s.credits, s.semester, s.subject_type, s.code
            FROM main_attendance m
            LEFT JOIN subjects s ON m.subject_code = s.short_code
            WHERE m.student_id = ?
            ORDER BY m.subject_code ASC
        ''', (student_id,))
        rows = cursor.fetchall()
        conn.close()
        
        subjects = []
        for r in rows:
            conducted = r[3]
            strictly_attended = r[1]
            dl_count = r[2]
            
            # Fetch relational UI identifiers safely
            full_name = r[4] if r[4] else f"Unknown ({r[0]})"
            credits = r[5] if r[5] is not None else 0
            semester = r[6] if r[6] else 6
            subject_type = r[7] if r[7] else "Core"
            actual_code = r[8] if r[8] else r[0]
            
            # Duty Leaves are counted as Present for calculation
            credited_attended = strictly_attended + dl_count
            missed = conducted - credited_attended
            percentage = round((credited_attended / conducted * 100) if conducted > 0 else 0)
            status_text = "Good" if percentage >= 75 else "At Risk"
            if percentage >= 90:
                status_text = "Excellent"
                
            subjects.append({
                "code": r[0],
                "actual_code": actual_code,
                "conducted": conducted,
                "attended": credited_attended,  # Now includes DL
                "dl_count": dl_count,
                "missed": missed,
                "percentage": percentage,
                "status_text": status_text,
                "full_name": full_name,
                "credits": credits,
                "semester": semester,
                "subject_type": subject_type
            })
        return subjects
    except Exception as e:
        print(f"Error fetching student attendance: {e}")
        return []

def get_teacher_details(user_id):
    """Fetch core profile attributes for a mapped teacher."""
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, department FROM teachers WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"name": row[0], "department": row[1]}
    except Exception as e:
        print(f"Error fetching teacher details: {e}")
    return None

def get_teacher_dashboard_data(user_id):
    """Aggregates all insights, mapped classes, and schedules natively securely into one payload."""
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Pull mapped class structures natively linking to global reference codes
        cursor.execute('''
            SELECT ts.subject_code, s.full_name, s.credits, s.semester, s.subject_type, s.code 
            FROM teacher_subjects ts
            LEFT JOIN subjects s ON ts.subject_code = s.short_code
            WHERE ts.user_id = ?
        ''', (user_id,))
        rows = cursor.fetchall()
        
        from datetime import datetime
        current_day = datetime.now().strftime('%A').upper()
        
        subjects = []
        total_enrolled = 0
        total_present = 0
        total_conducted = 0
        active_sessions_today = 0
        
        day_abbr = {"MONDAY": "Mon", "TUESDAY": "Tue", "WEDNESDAY": "Wed", "THURSDAY": "Thu", "FRIDAY": "Fri", "SATURDAY": "Sat", "SUNDAY": "Sun"}
        
        # Iterative nested processing tracking individual stats
        for r in rows:
            short_code = r[0]
            full_name = r[1] if r[1] else f"Unknown ({short_code})"
            sem = r[3] if r[3] else 0
            code = r[5] if r[5] else short_code
            
            # Sub-query distinct student enrollments via the cumulative database structure
            cursor.execute("SELECT COUNT(DISTINCT student_id), SUM(present_count + duty_leave_count), SUM(total_count) FROM main_attendance WHERE subject_code = ?", (short_code,))
            agg = cursor.fetchone()
            enrolled = agg[0] if agg and agg[0] else 0
            s_present = agg[1] if agg and agg[1] else 0
            s_conducted = agg[2] if agg and agg[2] else 0
            
            total_enrolled += enrolled
            total_present += s_present
            total_conducted += s_conducted
            
            # Build timetable combinations dynamically handling splits
            cursor.execute("SELECT DISTINCT day FROM timetable WHERE subject_code = ?", (short_code,))
            days = cursor.fetchall()
            day_order = {"MONDAY": 1, "TUESDAY": 2, "WEDNESDAY": 3, "THURSDAY": 4, "FRIDAY": 5, "SATURDAY": 6, "SUNDAY": 7}
            sorted_days = sorted(days, key=lambda x: day_order.get(x[0].upper(), 99))
            schedule_str = ", ".join([day_abbr.get(d[0], d[0][:3].capitalize()) for d in sorted_days]) if sorted_days else "No Schedule"
            
            # Check physical occurrences explicitly targeting today
            cursor.execute("SELECT COUNT(*) FROM timetable WHERE subject_code = ? AND day = ?", (short_code, current_day))
            sessions_count = cursor.fetchone()[0]
            active_sessions_today += sessions_count
            
            subjects.append({
                "short_code": short_code,
                "code": code,
                "full_name": full_name,
                "semester": sem,
                "enrolled": enrolled,
                "schedule": schedule_str
            })
            
        conn.close()
        
        avg_rate = int(round((total_present / total_conducted) * 100)) if total_conducted > 0 else 0
        
        return {
            "subjects": subjects,
            "total_enrolled": total_enrolled,
            "active_sessions": active_sessions_today,
            "avg_rate": avg_rate
        }
    except Exception as e:
        print(f"Error compiling teacher dashboard constraints: {e}")
        return {"subjects": [], "total_enrolled": 0, "active_sessions": 0, "avg_rate": 0}

def get_subject_manage_data(subject_code):
    """
    Fetch comprehensive analytics and student records for a specific subject.
    Returns: {
        "subject": { "name": "...", "code": "...", "sem": ... },
        "stats": { "total_classes": ..., "avg_attendance": ..., "total_dl": ..., "total_absences": ... },
        "students": [ { "id": "...", "name": "...", "attended": ..., "dl": ..., "total": ..., "percent": ..., "missed": ..., "status": "..." } ],
        "at_risk": [ ... ]
    }
    """
    db_path = Config.AUTH_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Fetch Subject Metadata
        cursor.execute("SELECT full_name, semester, code FROM subjects WHERE short_code = ?", (subject_code,))
        sub_row = cursor.fetchone()
        if not sub_row:
            conn.close()
            return None
            
        subject_info = {"name": sub_row[0], "sem": sub_row[1], "code": sub_row[2]}
        
        # 2. Fetch Student Records from main_attendance joined with students
        cursor.execute("""
            SELECT m.student_id, s.name, m.present_count, m.duty_leave_count, m.total_count, s.ktu_id
            FROM main_attendance m
            JOIN students s ON m.student_id = s.student_id
            WHERE m.subject_code = ?
            ORDER BY s.name ASC
        """, (subject_code,))
        rows = cursor.fetchall()
        
        students = []
        at_risk = []
        total_present_dl = 0
        total_conducted = 0
        total_dl = 0
        total_absences = 0
        max_conducted = 0
        
        for r in rows:
            sid, name, present, dl, total, ktu_id = r
            credited_present = present + dl
            missed = total - credited_present
            percent = float(round((credited_present / total * 100) if total > 0 else 0, 1))
            
            # Status classification
            status = "Safe"
            if percent < 75:
                status = "At Risk"
            elif percent < 85:
                status = "Warning"
                
            student_data = {
                "id": ktu_id if ktu_id else sid, # Prioritize KTU ID
                "name": name,
                "attended": present,
                "dl": dl,
                "total": total,
                "percent": percent,
                "missed": missed,
                "status": status
            }
            students.append(student_data)
            
            # Aggregate stats
            total_present_dl += credited_present
            total_conducted += total
            total_dl += dl
            total_absences += missed
            if total > max_conducted:
                max_conducted = total
                
        conn.close()
        
        avg_attendance = int(round((total_present_dl / total_conducted * 100))) if total_conducted > 0 else 0
        
        return {
            "subject": subject_info,
            "stats": {
                "total_classes": max_conducted,
                "avg_attendance": avg_attendance,
                "total_dl": total_dl,
                "total_absences": total_absences
            },
            "students": students,
            "at_risk": [s for s in students if s["status"] == "At Risk"]
        }
    except Exception as e:
        print(f"Error fetching subject manageable constraints: {e}")
        return None
