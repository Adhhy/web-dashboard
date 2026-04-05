"""
Duty Leave Module - Database Access Layer
All SQL operations for the duty_leave_requests table.
No business logic here — only raw DB reads/writes.
"""
import sqlite3
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


def _get_conn():
    conn = sqlite3.connect(Config.AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── STUDENT ────────────────────────────────────────────────────────────────

def get_student_subjects(student_id: str) -> list:
    """Return subjects the student can apply leave for (from timetable/subjects)."""
    conn = _get_conn()
    try:
        # Return all subjects in the system (the batch's subjects)
        rows = conn.execute("""
            SELECT code, full_name, short_code
            FROM subjects
            ORDER BY full_name
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_student_requests(student_id: str) -> dict:
    """Return pending and completed requests for a student."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT d.*, s.full_name as subject_name
            FROM duty_leave_requests d
            LEFT JOIN subjects s ON d.subject_code = s.short_code
            WHERE d.student_id = ?
            ORDER BY d.created_at DESC
        """, (student_id,)).fetchall()
        
        pending = []
        history = []
        for r in rows:
            req = dict(r)
            if req['current_state'] in ('PendingAdvisor', 'PendingFaculty', 'Locked'):
                pending.append(req)
            else:
                history.append(req)
        return {'pending': pending, 'history': history}
    finally:
        conn.close()


def create_request(student_id: str, subject_code: str, date_str: str,
                   periods: str, reason: str, description: str,
                   evidence_path: str = None) -> int:
    """Insert a new duty leave request. Returns the new row id."""
    conn = _get_conn()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = conn.execute("""
            INSERT INTO duty_leave_requests
            (student_id, subject_code, date, periods, reason, description,
             evidence_path, advisor_status, faculty_status, admin_status,
             current_state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', 'Pending', 'Pending',
                    'PendingAdvisor', ?, ?)
        """, (student_id, subject_code, date_str, periods, reason,
              description, evidence_path, now, now))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_request_by_id(request_id: int) -> dict | None:
    """Fetch a single request by id."""
    conn = _get_conn()
    try:
        row = conn.execute("""
            SELECT d.*, s.full_name as subject_name, st.name as student_name,
                   st.ktu_id, st.batch, st.department
            FROM duty_leave_requests d
            LEFT JOIN subjects s ON d.subject_code = s.short_code
            LEFT JOIN students st ON d.student_id = st.student_id
            WHERE d.id = ?
        """, (request_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_request(request_id: int) -> bool:
    """Hard delete a request from the database."""
    conn = _get_conn()
    try:
        cursor = conn.execute("DELETE FROM duty_leave_requests WHERE id = ?", (request_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ─── ADVISOR ────────────────────────────────────────────────────────────────

def get_advisor_requests(advisor_user_id: int) -> dict:
    """Return requests visible to the advisor (all students in their batch)."""
    conn = _get_conn()
    try:
        # Get advisor's batch
        adv_row = conn.execute("""
            SELECT batch FROM advisors WHERE user_id = ?
        """, (advisor_user_id,)).fetchone()
        
        if not adv_row:
            return {'pending': [], 'history': [], 'stats': {}}
        
        batch = adv_row['batch']
        
        rows = conn.execute("""
            SELECT d.*, s.full_name as subject_name, st.name as student_name,
                   st.ktu_id, st.batch, st.department
            FROM duty_leave_requests d
            LEFT JOIN subjects s ON d.subject_code = s.short_code
            LEFT JOIN students st ON d.student_id = st.student_id
            WHERE st.batch = ?
            ORDER BY d.created_at DESC
        """, (batch,)).fetchall()
        
        pending = []
        history = []
        for r in rows:
            req = dict(r)
            if req['current_state'] == 'PendingAdvisor':
                pending.append(req)
            elif req['current_state'] not in ('PendingAdvisor',):
                history.append(req)

        total = len(pending) + len(history)
        approved = sum(1 for r in history if r['current_state'] in ('Approved', 'Completed'))
        
        stats = {
            'total': total,
            'pending': len(pending),
            'approved': approved,
        }
        return {'pending': pending, 'history': history, 'stats': stats}
    finally:
        conn.close()


def advisor_action(request_id: int, action: str) -> bool:
    """Advisor approves or rejects. Updates state accordingly."""
    conn = _get_conn()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if action == 'approve':
            conn.execute("""
                UPDATE duty_leave_requests
                SET advisor_status='Approved', current_state='PendingFaculty', updated_at=?
                WHERE id=? AND current_state='PendingAdvisor'
            """, (now, request_id))
        else:
            conn.execute("""
                UPDATE duty_leave_requests
                SET advisor_status='Rejected', current_state='Rejected', updated_at=?
                WHERE id=? AND current_state='PendingAdvisor'
            """, (now, request_id))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


# ─── FACULTY ────────────────────────────────────────────────────────────────

def get_faculty_requests(teacher_user_id: int) -> dict:
    """Return requests for subjects handled by this teacher."""
    conn = _get_conn()
    try:
        # Get the subject codes this teacher handles
        subject_rows = conn.execute("""
            SELECT subject_code FROM teacher_subjects WHERE user_id = ?
        """, (teacher_user_id,)).fetchall()
        
        if not subject_rows:
            return {'pending': [], 'history': [], 'stats': {}}
        
        codes = [r['subject_code'] for r in subject_rows]
        placeholders = ','.join('?' * len(codes))
        
        rows = conn.execute(f"""
            SELECT d.*, s.full_name as subject_name, st.name as student_name,
                   st.ktu_id, st.batch, st.department
            FROM duty_leave_requests d
            LEFT JOIN subjects s ON d.subject_code = s.short_code
            LEFT JOIN students st ON d.student_id = st.student_id
            WHERE d.subject_code IN ({placeholders})
            ORDER BY d.created_at DESC
        """, codes).fetchall()
        
        pending = []
        history = []
        for r in rows:
            req = dict(r)
            if req['current_state'] == 'PendingFaculty':
                pending.append(req)
            else:
                history.append(req)
        
        stats = {
            'total': len(pending) + len(history),
            'pending': len(pending),
            'approved': sum(1 for r in history if r['current_state'] in ('Approved', 'Completed')),
        }
        return {'pending': pending, 'history': history, 'stats': stats}
    finally:
        conn.close()


def _apply_attendance_credit(conn, request_id: int):
    """
    Internal helper to increment duty_leave_count in main_attendance.
    Called within an active transaction.
    """
    row = conn.execute("""
        SELECT student_id, subject_code, periods 
        FROM duty_leave_requests WHERE id = ?
    """, (request_id,)).fetchone()
    
    if not row:
        return
    
    student_id = row['student_id']
    subject_code = row['subject_code']
    periods_str = row['periods']
    
    # Calculate number of periods (e.g., "1,2,3" -> 3)
    # We assume the user's confirmation that they are single digits P1-P7.
    if not periods_str:
        return
        
    p_list = [p.strip() for p in periods_str.split(',') if p.strip()]
    count = len(p_list)
    
    # Update cumulative attendance
    # We increment both duty_leave_count and total_count.
    # If the calculator already processed 'A' for this slot, total_count was already incremented.
    # However, to maintain alignment with the 'total' vs 'present+dl' logic, we ensure it's recorded.
    conn.execute("""
        UPDATE main_attendance 
        SET duty_leave_count = duty_leave_count + ?,
            total_count = total_count + ?
        WHERE student_id = ? AND subject_code = ?
    """, (count, count, student_id, subject_code))


def faculty_action(request_id: int, action: str) -> bool:
    """Faculty approves or rejects a PendingFaculty request."""
    conn = _get_conn()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("BEGIN TRANSACTION")
        
        if action == 'approve':
            conn.execute("""
                UPDATE duty_leave_requests
                SET faculty_status='Approved', current_state='Completed', updated_at=?
                WHERE id=? AND current_state='PendingFaculty'
            """, (now, request_id))
            
            if conn.total_changes > 0:
                _apply_attendance_credit(conn, request_id)
        else:
            conn.execute("""
                UPDATE duty_leave_requests
                SET faculty_status='Rejected', current_state='Rejected', updated_at=?
                WHERE id=? AND current_state='PendingFaculty'
            """, (now, request_id))
            
        conn.commit()
        return conn.total_changes > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── ADMIN ──────────────────────────────────────────────────────────────────

def get_admin_requests() -> dict:
    """Return locked requests (admin override queue) plus recent history."""
    conn = _get_conn()
    try:
        locked = conn.execute("""
            SELECT d.*, s.full_name as subject_name, st.name as student_name,
                   st.ktu_id, st.batch, st.department
            FROM duty_leave_requests d
            LEFT JOIN subjects s ON d.subject_code = s.short_code
            LEFT JOIN students st ON d.student_id = st.student_id
            WHERE d.current_state = 'Locked'
            ORDER BY d.created_at DESC
        """).fetchall()
        
        history = conn.execute("""
            SELECT d.*, s.full_name as subject_name, st.name as student_name,
                   st.ktu_id, st.batch, st.department
            FROM duty_leave_requests d
            LEFT JOIN subjects s ON d.subject_code = s.short_code
            LEFT JOIN students st ON d.student_id = st.student_id
            WHERE d.current_state IN ('Completed', 'Approved', 'Rejected')
            ORDER BY d.updated_at DESC
            LIMIT 50
        """).fetchall()
        
        stats = {
            'locked': len(locked),
            'total_history': len(history),
        }
        return {
            'locked': [dict(r) for r in locked],
            'history': [dict(r) for r in history],
            'stats': stats,
        }
    finally:
        conn.close()


def admin_action(request_id: int, action: str) -> bool:
    """Admin override: approve or reject a Locked request."""
    conn = _get_conn()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_state = 'Completed' if action == 'approve' else 'Rejected'
        conn.execute("BEGIN TRANSACTION")
        
        conn.execute("""
            UPDATE duty_leave_requests
            SET admin_status=?, current_state=?, updated_at=?
            WHERE id=? AND current_state='Locked'
        """, ('Approved' if action == 'approve' else 'Rejected', new_state, now, request_id))
        
        if action == 'approve' and conn.total_changes > 0:
            _apply_attendance_credit(conn, request_id)
            
        conn.commit()
        return conn.total_changes > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── LOCK SWEEP ─────────────────────────────────────────────────────────────

def lock_expired_requests() -> int:
    """
    Lock all PendingAdvisor requests that were submitted on a previous day.
    Returns the number of requests locked.
    """
    conn = _get_conn()
    try:
        from datetime import date
        today = date.today().isoformat()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            UPDATE duty_leave_requests
            SET current_state='Locked', updated_at=?
            WHERE current_state='PendingAdvisor' AND date < ?
        """, (now, today))
        conn.commit()
        return conn.total_changes
    finally:
        conn.close()
