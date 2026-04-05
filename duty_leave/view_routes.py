"""
Duty Leave Module - View Routes (Page Renders)
All GET routes that serve HTML pages for the duty leave portal.
Replaces the old static routes in app.py.
"""
from flask import render_template, session, redirect, url_for
from duty_leave import duty_leave_views
from duty_leave import services


# ─── STUDENT ────────────────────────────────────────────────────────────────

@duty_leave_views.route('/student/duty-leave')
def student_duty_leave_page():
    """Render the student duty leave portal with real data."""
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    
    from utils.helpers import get_student_details
    student = get_student_details(session['user_id'])
    if not student:
        return redirect(url_for('login'))

    data = services.get_student_portal_data(student['student_id'])
    return render_template('student_duty_leave.html', student=student, **data)


# ─── ADVISOR ────────────────────────────────────────────────────────────────

@duty_leave_views.route('/advisor/duty-leave')
def advisor_duty_leave_page():
    """Render the advisor duty leave portal with real data."""
    if 'user_id' not in session or session.get('role') != 'advisor':
        return redirect(url_for('login'))
    
    from utils.helpers import get_advisor_details
    advisor = get_advisor_details(session['user_id'])
    
    data = services.get_advisor_portal_data(session['user_id'])
    return render_template('advisor_duty_leave.html', advisor=advisor, **data)


# ─── FACULTY / TEACHER ──────────────────────────────────────────────────────

@duty_leave_views.route('/teacher/duty-leave')
def faculty_duty_leave_page():
    """Render the teacher/faculty duty leave portal with real data."""
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    from utils.helpers import get_teacher_details
    teacher = get_teacher_details(session['user_id'])
    
    data = services.get_faculty_portal_data(session['user_id'])
    return render_template('teacher_duty_leave.html', teacher=teacher, **data)


# ─── ADMIN ──────────────────────────────────────────────────────────────────

@duty_leave_views.route('/admin/duty-leave')
def admin_duty_leave_page():
    """Render the admin duty leave portal — shows only Locked requests."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    data = services.get_admin_portal_data()
    return render_template('admin_duty_leave.html', **data)
