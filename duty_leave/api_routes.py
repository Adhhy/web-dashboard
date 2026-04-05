"""
Duty Leave Module - API Routes (JSON Actions)
All POST endpoints that handle duty leave workflow actions.
Returns JSON responses consumed by the page-level JavaScript.
"""
import os
from flask import request, session, jsonify, current_app
from duty_leave import duty_leave_api
from duty_leave import services


def _get_upload_folder():
    return os.path.join(current_app.static_folder, 'uploads', 'duty_leave')


# ─── STUDENT: Submit Request ─────────────────────────────────────────────────

@duty_leave_api.route('/api/duty-leave/submit', methods=['POST'])
def api_submit_request():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from utils.helpers import get_student_details
    student = get_student_details(session['user_id'])
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'}), 404
    
    file = request.files.get('evidence')
    result = services.submit_request(
        form_data=request.form,
        file=file,
        student_id=student['student_id'],
        upload_folder=_get_upload_folder(),
    )
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ─── STUDENT: Delete Request ─────────────────────────────────────────────────

@duty_leave_api.route('/api/duty-leave/delete', methods=['POST'])
def api_delete_request():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from utils.helpers import get_student_details
    student = get_student_details(session['user_id'])
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'}), 404
    
    data = request.get_json(silent=True) or request.form
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({'success': False, 'message': 'request_id is required'}), 400
    
    result = services.delete_student_request(
        request_id=int(request_id),
        student_id=student['student_id'],
        static_folder=current_app.static_folder,
    )
    return jsonify(result), 200 if result['success'] else 400


# ─── ADVISOR: Approve / Reject ───────────────────────────────────────────────

@duty_leave_api.route('/api/duty-leave/advisor/action', methods=['POST'])
def api_advisor_action():
    if 'user_id' not in session or session.get('role') != 'advisor':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json(silent=True) or request.form
    request_id = data.get('request_id')
    action = data.get('action')
    
    if not request_id or not action:
        return jsonify({'success': False, 'message': 'request_id and action are required'}), 400
    
    result = services.process_advisor_action(int(request_id), action, session['user_id'])
    return jsonify(result), 200 if result['success'] else 400


# ─── FACULTY: Approve / Reject ───────────────────────────────────────────────

@duty_leave_api.route('/api/duty-leave/faculty/action', methods=['POST'])
def api_faculty_action():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json(silent=True) or request.form
    request_id = data.get('request_id')
    action = data.get('action')
    
    if not request_id or not action:
        return jsonify({'success': False, 'message': 'request_id and action are required'}), 400
    
    result = services.process_faculty_action(int(request_id), action, session['user_id'])
    return jsonify(result), 200 if result['success'] else 400


# ─── ADMIN: Override ─────────────────────────────────────────────────────────

@duty_leave_api.route('/api/duty-leave/admin/action', methods=['POST'])
def api_admin_action():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json(silent=True) or request.form
    request_id = data.get('request_id')
    action = data.get('action')
    
    if not request_id or not action:
        return jsonify({'success': False, 'message': 'request_id and action are required'}), 400
    
    result = services.process_admin_action(int(request_id), action)
    return jsonify(result), 200 if result['success'] else 400


# ─── STATUS CHECK ────────────────────────────────────────────────────────────

@duty_leave_api.route('/api/duty-leave/requests', methods=['GET'])
def api_get_my_requests():
    """Returns JSON of requests for the current user's role."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    role = session.get('role')
    if role == 'student':
        from utils.helpers import get_student_details
        student = get_student_details(session['user_id'])
        if not student:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        from duty_leave.models import get_student_requests
        data = get_student_requests(student['student_id'])
    elif role == 'advisor':
        from duty_leave.models import get_advisor_requests
        data = get_advisor_requests(session['user_id'])
    elif role == 'teacher':
        from duty_leave.models import get_faculty_requests
        data = get_faculty_requests(session['user_id'])
    elif role == 'admin':
        from duty_leave.models import get_admin_requests
        data = get_admin_requests()
    else:
        return jsonify({'success': False, 'message': 'Unsupported role'}), 400
    
    return jsonify({'success': True, 'data': data})
