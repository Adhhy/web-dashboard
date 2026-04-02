import sqlite3
from datetime import datetime
from config import Config

class AttendanceService:
    @staticmethod
    def get_db_connection():
        return sqlite3.connect(Config.AUTH_DB_PATH)

    @staticmethod
    def get_current_session():
        """Retrieve the most recent active session."""
        conn = AttendanceService.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM sessions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[1] == 'active':
            return {"id": row[0], "status": row[1]}
        return None

    @staticmethod
    def get_session_info(now):
        """Determine period and session type based on current time."""
        from datetime import time
        t = now.time()
        
        # Morning boundaries
        if time(8, 0) <= t <= time(12, 30):
            session_type = "Morning"
            if t <= time(9, 25): period = "P1"
            elif t <= time(10, 20): period = "P2"
            elif t <= time(11, 30): period = "P3"
            else: period = "P4"
            return session_type, period
        
        # Afternoon boundaries
        if time(13, 0) <= t <= time(16, 30):
            session_type = "Afternoon"
            if t <= time(14, 10): period = "P5"
            elif t <= time(15, 5): period = "P6"
            else: period = "P7"
            return session_type, period
            
        return "Unknown", "P0"

    @staticmethod
    def submit_log(data):
        """
        Ingest a log from a client device.
        Requires data: device_id, student_id, student_name, recognition_status, 
        event_type ('ENTRY' or 'EXIT'), late_entry, bus_delay
        """
        now = datetime.now()
        session = AttendanceService.get_current_session()
        if not session:
            return {"success": False, "message": "No active session. Log rejected."}

        device_id = data.get('device_id')
        student_id = data.get('student_id')
        student_name = data.get('student_name', 'Unknown')
        recognition_status = data.get('recognition_status', 'Unknown')
        event_type = data.get('event_type', 'ENTRY').upper()
        late_entry = 1 if data.get('late_entry') else 0
        bus_delay = 1 if data.get('bus_delay') else 0
        
        # Auto-categorize
        session_type, period = AttendanceService.get_session_info(now)
        date_str = now.strftime('%Y-%m-%d')

        # Formatting long system message
        # [Period - EventType] <Message>. Alert: <ApprovalStatus>
        if late_entry or bus_delay:
            status = 'pending'
            alerts = []
            if late_entry: alerts.append("Late entry detected")
            if bus_delay: alerts.append("Bus delay reported")
            message = " ".join(alerts)
            alert_status = "Requires advisor approval"
        else:
            status = 'approved'
            message = "Normal entry" if event_type == 'ENTRY' else "Normal exit"
            alert_status = "Automatically approved"
            
        system_message = f"[{period} - {event_type}] {message}. Alert: {alert_status}."

        try:
            conn = AttendanceService.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO policy_logs (
                    session_id, device_id, student_id, student_name, recognition_status,
                    event_type, period, session_type, date, 
                    late_entry, bus_delay, status, system_message, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session['id'], device_id, student_id, student_name, recognition_status,
                  event_type, period, session_type, date_str,
                  late_entry, bus_delay, status, system_message, now.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return {"success": True, "message": "Log recorded.", "status": status, "period": period}
        except Exception as e:
            print(f"Error submitting log: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_active_session_logs():
        """Fetch logs associated with the latest session."""
        conn = AttendanceService.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM sessions ORDER BY id DESC LIMIT 1")
        session_row = cursor.fetchone()
        if not session_row:
            conn.close()
            return []
        
        session_id = session_row[0]
        
        cursor.execute("""
            SELECT id, device_id, student_id, student_name, timestamp, 
                   recognition_status, status, system_message 
            FROM policy_logs 
            WHERE session_id = ? 
            ORDER BY timestamp DESC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for r in rows:
            logs.append({
                "id": r[0],
                "device_id": r[1],
                "student_id": r[2],
                "student_name": r[3],
                "timestamp": r[4],
                "recognition_status": r[5],
                "status": r[6],
                "system_message": r[7]
            })
        return logs

    @staticmethod
    def process_advisor_action(log_id, action, advisor_id):
        """Approve or reject a pending log."""
        if action not in ['approved', 'rejected']:
            return {"success": False, "message": "Invalid action."}

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            conn = AttendanceService.get_db_connection()
            cursor = conn.cursor()
            
            # Verify the log exists and is pending
            cursor.execute("SELECT status FROM policy_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return {"success": False, "message": "Log not found."}
            if row[0] != 'pending':
                conn.close()
                return {"success": False, "message": f"Log is already {row[0]}."}

            cursor.execute("""
                UPDATE policy_logs 
                SET status = ?, advisor_id = ?, action_timestamp = ? 
                WHERE id = ?
            """, (action, advisor_id, timestamp, log_id))
            
            conn.commit()
            conn.close()
            return {"success": True, "message": f"Log {action} successfully."}
        except Exception as e:
            print(f"Error processing advisor action: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def is_session_finalized(session_type, date):
        """Check if a session for a given date has been finalized."""
        from database.database import is_session_finalized as db_check
        return db_check(session_type, date)


