from flask import Blueprint, request, jsonify, session
from attendance.service import AttendanceService
from functools import wraps
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

def advisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'advisor':
            return jsonify({"success": False, "message": "Advisor access required."}), 403
        return f(*args, **kwargs)
    return decorated_function

@attendance_bp.route('/api/attendance/log', methods=['POST'])
def submit_log():
    """Endpoint for client devices to send policy logs."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON data."}), 400
        
    result = AttendanceService.submit_log(data)
    if result['success']:
        return jsonify(result), 200
    else:
        # If no active session, it returns False
        return jsonify(result), 403

@attendance_bp.route('/api/attendance/logs', methods=['GET'])
@advisor_required
def get_logs():
    """Endpoint for advisor dashboard to fetch logs for the current session."""
    logs = AttendanceService.get_active_session_logs()
    return jsonify({"success": True, "logs": logs}), 200

@attendance_bp.route('/api/attendance/action/<int:log_id>', methods=['POST'])
@advisor_required
def process_action(log_id):
    """Endpoint for advisor to approve or reject a pending log."""
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({"success": False, "message": "Missing action field."}), 400
        
    action = data.get('action')
    advisor_id = session.get('user_id')
    
    result = AttendanceService.process_advisor_action(log_id, action, advisor_id)
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@attendance_bp.route('/api/attendance/finalize', methods=['POST'])
@advisor_required
def finalize_session():
    """Trigger the final calculation of attendance for the current session."""
    from attendance.session_manager import SessionManager
    from attendance.service import AttendanceService
    from datetime import time
    
    # 1. Prevent finalization during an active session
    current_session = AttendanceService.get_current_session()
    if current_session and current_session['status'] == 'active':
        return jsonify({
            "success": False, 
            "message": "Cannot finalize while a session is ACTIVE. Please stop the session first."
        }), 400

    # 2. Determine session type based on database status and current time
    now = datetime.now()

    today = now.strftime('%Y-%m-%d')
    morning_end = datetime.combine(now.date(), time(12, 25))
    afternoon_end = datetime.combine(now.date(), time(16, 0))
    
    target_session = None
    
    # Prioritize Morning session if unfinished
    if not AttendanceService.is_session_finalized("Morning", today):
        if now >= morning_end:
            target_session = "Morning"
        else:
            return jsonify({
                "success": False, 
                "message": "Morning session cannot be finalized before 12:25 PM."
            }), 400
    
    # If Morning is done, look for Afternoon
    if not target_session:
        if not AttendanceService.is_session_finalized("Afternoon", today):
            if now >= afternoon_end:
                target_session = "Afternoon"
            else:
                return jsonify({
                    "success": False, 
                    "message": "Morning is finalized. Afternoon cannot be finalized before 4:00 PM."
                }), 400
        else:
            return jsonify({
                "success": False, 
                "message": "Both sessions for today have already been finalized."
            }), 400

    manager = SessionManager()
    # Note: finalize_session internally clears logs ONLY for the targeted session
    success = manager.finalize_session(target_session)
    
    if success:
        return jsonify({
            "success": True, 
            "message": f"{target_session} session finalized successfully."
        }), 200
    else:
        return jsonify({
            "success": False, 
            "message": f"Finalization of {target_session} failed. Check system logs."
        }), 500
@attendance_bp.route('/api/attendance/calculate', methods=['POST'])
@advisor_required
def calculate_attendance():
    """Trigger the subject-wise calculation for the target session."""
    from attendance.calculator import AttendanceCalculator
    from datetime import datetime
    
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    # 1. Determine target session (similar to finalize_session logic)
    target_session = None
    
    # Morning check
    if not AttendanceCalculator.is_session_calculated("Morning", today):
        # We assume calculation is allowed after session finalization
        # Here we check if records exist in morning_attendance to process
        target_session = "Morning"
    else:
        # If Morning is done, check for Afternoon
        if not AttendanceCalculator.is_session_calculated("Afternoon", today):
            target_session = "Afternoon"
        else:
            return jsonify({
                "success": False, 
                "message": "Both sessions for today have already been calculated into the main records."
            }), 400

    # 2. Process Calculation
    result = AttendanceCalculator.process_session(target_session, today)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400
