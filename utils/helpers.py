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
