"""
Duty Leave Module - Business Logic / Service Layer
Validates, orchestrates, and delegates to models.
"""
import os
from werkzeug.utils import secure_filename
from duty_leave import models
from duty_leave.utils import is_past_deadline, today_str, get_state_display, get_state_badge_class, format_periods

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _enrich_request(req: dict) -> dict:
    """Add display fields to a raw DB row dict."""
    req['state_display'] = get_state_display(req.get('current_state', ''))
    req['state_class'] = get_state_badge_class(req.get('current_state', ''))
    req['periods_display'] = format_periods(req.get('periods', ''))
    return req


def run_lock_sweep():
    """Called at the start of each duty leave page load to lock expired requests."""
    return models.lock_expired_requests()


# ─── STUDENT ────────────────────────────────────────────────────────────────

def get_student_portal_data(student_id: str) -> dict:
    """Prepares all data needed for the student duty leave page."""
    run_lock_sweep()
    data = models.get_student_requests(student_id)
    subjects = models.get_student_subjects(student_id)
    
    pending = [_enrich_request(r) for r in data['pending']]
    history = [_enrich_request(r) for r in data['history']]
    
    return {
        'subjects': subjects,
        'pending_requests': pending,
        'completed_requests': history,
        'today': today_str(),
    }


def submit_request(form_data: dict, file=None, student_id: str = '', upload_folder: str = '') -> dict:
    """Validate and create a new duty leave request."""
    subject_code = form_data.get('subject_code', '').strip()
    periods = form_data.get('periods', '').strip()
    reason = form_data.get('reason', '').strip()
    description = form_data.get('description', '').strip()

    if not subject_code or not periods or not reason:
        return {'success': False, 'message': 'Subject, periods, and reason are required.'}

    evidence_path = None
    if file and file.filename:
        if not _allowed_file(file.filename):
            return {'success': False, 'message': 'Invalid file type. Only PDF, JPG, PNG allowed.'}
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_BYTES:
            return {'success': False, 'message': 'File exceeds 2MB limit.'}
        
        student_folder = os.path.join(upload_folder, student_id)
        os.makedirs(student_folder, exist_ok=True)
        filename = secure_filename(file.filename)
        save_path = os.path.join(student_folder, filename)
        file.save(save_path)
        # Store relative URL path
        evidence_path = f'uploads/duty_leave/{student_id}/{filename}'

    request_id = models.create_request(
        student_id=student_id,
        subject_code=subject_code,
        date_str=today_str(),
        periods=periods,
        reason=reason,
        description=description,
        evidence_path=evidence_path,
    )
    return {'success': True, 'request_id': request_id, 'message': 'Request submitted successfully.'}


def delete_student_request(request_id: int, student_id: str, static_folder: str) -> dict:
    """Validate ownership and state, then delete the request and its evidence file."""
    req = models.get_request_by_id(request_id)
    if not req:
        return {'success': False, 'message': 'Request not found.'}
    
    # Ownership Check
    if req['student_id'] != student_id:
        return {'success': False, 'message': 'Permission denied: This is not your request.'}
    
    # State Check: Only PendingAdvisor or PendingFaculty allowed
    if req['current_state'] not in ('PendingAdvisor', 'PendingFaculty'):
        msg = f"Cannot delete request in state: {req['current_state']}"
        if req['current_state'] == 'Locked':
            msg = "Fallback mechanism activated. Requests sent to Admin cannot be deleted."
        return {'success': False, 'message': msg}
    
    # File Cleanup (if evidence exists)
    if req.get('evidence_path'):
        # evidence_path is relative like 'uploads/duty_leave/...'
        abs_path = os.path.join(static_folder, req['evidence_path'])
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception:
                pass # Continue even if file delete fails
    
    # DB Deletion
    ok = models.delete_request(request_id)
    if ok:
        return {'success': True, 'message': 'Request deleted successfully.'}
    return {'success': False, 'message': 'Database deletion failed.'}


# ─── ADVISOR ────────────────────────────────────────────────────────────────

def get_advisor_portal_data(advisor_user_id: int) -> dict:
    """Prepares all data needed for the advisor duty leave page."""
    run_lock_sweep()
    data = models.get_advisor_requests(advisor_user_id)
    
    pending = [_enrich_request(r) for r in data['pending']]
    history = [_enrich_request(r) for r in data['history']]
    
    return {
        'pending_requests': pending,
        'history': history,
        'stats': data['stats'],
        'today': today_str(),
    }


def process_advisor_action(request_id: int, action: str, advisor_user_id: int) -> dict:
    """Validate and perform advisor approve/reject."""
    if action not in ('approve', 'reject'):
        return {'success': False, 'message': 'Invalid action.'}
    
    req = models.get_request_by_id(request_id)
    if not req:
        return {'success': False, 'message': 'Request not found.'}
    if req['current_state'] != 'PendingAdvisor':
        return {'success': False, 'message': f"Cannot act on request in state: {req['current_state']}"}
    
    ok = models.advisor_action(request_id, action)
    if ok:
        msg = 'Approved — forwarded to faculty.' if action == 'approve' else 'Request rejected.'
        return {'success': True, 'message': msg}
    return {'success': False, 'message': 'Action failed. The request may have been modified.'}


# ─── FACULTY ────────────────────────────────────────────────────────────────

def get_faculty_portal_data(teacher_user_id: int) -> dict:
    """Prepares all data needed for the faculty duty leave page."""
    run_lock_sweep()
    data = models.get_faculty_requests(teacher_user_id)
    
    pending = [_enrich_request(r) for r in data['pending']]
    history = [_enrich_request(r) for r in data['history']]
    
    return {
        'pending_requests': pending,
        'history': history,
        'stats': data['stats'],
        'today': today_str(),
    }


def process_faculty_action(request_id: int, action: str, teacher_user_id: int) -> dict:
    """Validate and perform faculty approve/reject."""
    if action not in ('approve', 'reject'):
        return {'success': False, 'message': 'Invalid action.'}
    
    req = models.get_request_by_id(request_id)
    if not req:
        return {'success': False, 'message': 'Request not found.'}
    if req['current_state'] != 'PendingFaculty':
        return {'success': False, 'message': f"Cannot act on request in state: {req['current_state']}"}
    
    ok = models.faculty_action(request_id, action)
    if ok:
        msg = 'Approved — duty leave granted.' if action == 'approve' else 'Request rejected.'
        return {'success': True, 'message': msg}
    return {'success': False, 'message': 'Action failed. The request may have been modified.'}


# ─── ADMIN ──────────────────────────────────────────────────────────────────

def get_admin_portal_data() -> dict:
    """Prepares all data needed for the admin duty leave page."""
    run_lock_sweep()
    data = models.get_admin_requests()
    
    locked = [_enrich_request(r) for r in data['locked']]
    history = [_enrich_request(r) for r in data['history']]
    
    return {
        'locked_requests': locked,
        'history': history,
        'stats': data['stats'],
        'today': today_str(),
    }


def process_admin_action(request_id: int, action: str) -> dict:
    """Validate and perform admin override on a Locked request."""
    if action not in ('approve', 'reject'):
        return {'success': False, 'message': 'Invalid action.'}
    
    req = models.get_request_by_id(request_id)
    if not req:
        return {'success': False, 'message': 'Request not found.'}
    if req['current_state'] != 'Locked':
        return {'success': False, 'message': f"Can only override Locked requests. Current: {req['current_state']}"}
    
    ok = models.admin_action(request_id, action)
    if ok:
        msg = 'Override applied — duty leave granted.' if action == 'approve' else 'Override applied — request rejected.'
        return {'success': True, 'message': msg}
    return {'success': False, 'message': 'Action failed.'}
