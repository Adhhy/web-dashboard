import sqlite3
from typing import List, Dict, Optional
from config import Config

class DeviceService:
    @staticmethod
    def get_db_connection():
        conn = sqlite3.connect(Config.AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def add_device_request(device_id: str, device_name: str, device_key: str, ip_address: Optional[str] = None) -> bool:
        """Stores a new connection request."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                # Check if there is already a pending request for this device
                cursor.execute('SELECT id FROM device_requests WHERE device_id = ? AND status = "pending"', (device_id,))
                if cursor.fetchone():
                    # Update existing request
                    cursor.execute('''
                        UPDATE device_requests SET device_name = ?, device_key = ?, ip_address = ?, created_at = CURRENT_TIMESTAMP
                        WHERE device_id = ? AND status = "pending"
                    ''', (device_name, device_key, ip_address, device_id))
                else:
                    # Insert new request
                    cursor.execute('''
                        INSERT INTO device_requests (device_id, device_name, device_key, ip_address)
                        VALUES (?, ?, ?, ?)
                    ''', (device_id, device_name, device_key, ip_address))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding device request: {e}")
            return False

    @staticmethod
    def get_pending_requests() -> List[Dict]:
        """Returns all pending device requests."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, device_id, device_name, device_key, ip_address, status, created_at 
                    FROM device_requests 
                    WHERE status = "pending"
                    ORDER BY created_at DESC
                ''')
                requests = cursor.fetchall()
                return [dict(ix) for ix in requests]
        except Exception as e:
            print(f"Error fetching pending requests: {e}")
            return []

    @staticmethod
    def approve_device(device_id: str, entered_key: str) -> bool:
        """Verifies the key and moves the device to the devices table."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Fetch the pending request
                cursor.execute('''
                    SELECT device_name, device_key, ip_address FROM device_requests
                    WHERE device_id = ? AND status = 'pending'
                ''', (device_id,))
                
                request = cursor.fetchone()
                if not request:
                    return False
                
                # Verify key
                if request['device_key'] != entered_key:
                    return False
                    
                device_name = request['device_name']
                device_key = request['device_key']
                ip_address = request['ip_address']

                # Mark request as approved
                cursor.execute('''
                    UPDATE device_requests SET status = 'approved' WHERE device_id = ? AND status = 'pending'
                ''', (device_id,))

                # Always treat as a new entry: delete old one if it exists
                cursor.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
                
                # Insert new device entry
                cursor.execute('''
                    INSERT INTO devices (device_id, device_name, device_key, ip_address, connection_status)
                    VALUES (?, ?, ?, ?, 'connected')
                ''', (device_id, device_name, device_key, ip_address))
                    
                conn.commit()
                return True
        except Exception as e:
            print(f"Error approving device: {e}")
            return False

    @staticmethod
    def reject_device(device_id: str) -> bool:
        """Marks a device request as rejected."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE device_requests SET status = 'rejected' WHERE device_id = ? AND status = 'pending'
                ''', (device_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error rejecting device: {e}")
            return False

    @staticmethod
    def get_devices() -> List[Dict]:
        """Returns all approved devices."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, device_id, device_name, ip_address, connection_status, approved_timestamp 
                    FROM devices
                    ORDER BY device_name ASC
                ''')
                devices = cursor.fetchall()
                return [dict(ix) for ix in devices]
        except Exception as e:
            print(f"Error fetching devices: {e}")
            return []

    @staticmethod
    def get_device_info(device_id: str) -> Optional[Dict]:
        """Returns details for a specific device."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, device_id, device_name, ip_address, connection_status, approved_timestamp 
                    FROM devices
                    WHERE device_id = ?
                ''', (device_id,))
                device = cursor.fetchone()
                return dict(device) if device else None
        except Exception as e:
            print(f"Error fetching device info: {e}")
            return None

    @staticmethod
    def disconnect_device(device_id: str) -> bool:
        """Marks a device as disconnected (Admin version)."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM devices WHERE device_id = ?
                ''', (device_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error disconnecting device: {e}")
            return False

    @staticmethod
    def disconnect_device_with_key(device_id: str, device_key: str) -> bool:
        """Verifies key and marks a device as disconnected (Device version)."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                # Verify key first
                cursor.execute('SELECT id FROM devices WHERE device_id = ? AND device_key = ?', (device_id, device_key))
                if not cursor.fetchone():
                    return False
                
                cursor.execute('''
                    DELETE FROM devices WHERE device_id = ?
                ''', (device_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error disconnecting device with key: {e}")
            return False

    @staticmethod
    def is_device_approved(device_id: str, device_key: str) -> Dict:
        """Checks if a device is approved without admin requirements."""
        try:
            with DeviceService.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check device_requests table
                cursor.execute('SELECT status FROM device_requests WHERE device_id = ? AND device_key = ?', (device_id, device_key))
                request = cursor.fetchone()
                
                if request:
                    status = request['status']
                    # Verify if it's also in the devices table if approved
                    if status == 'approved':
                        cursor.execute('SELECT connection_status FROM devices WHERE device_id = ?', (device_id,))
                        device = cursor.fetchone()
                        return {
                            'status': 'approved',
                            'connection_status': 'connected' if device else 'disconnected'
                        }
                    return {'status': status}
                
                return {'status': 'not_found'}
        except Exception as e:
            print(f"Error checking device status: {e}")
            return {'status': 'error', 'message': str(e)}
