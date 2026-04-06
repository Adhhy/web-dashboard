import os
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from config import Config
from auth.auth_handler import auth_bp
from attendance import attendance_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp)
app.register_blueprint(attendance_bp)

from routes.system_routes import system_bp
app.register_blueprint(system_bp)

# Register the Duty Leave module blueprints
from duty_leave import duty_leave_views, duty_leave_api
app.register_blueprint(duty_leave_views)
app.register_blueprint(duty_leave_api)

# Ensure upload directory exists
os.makedirs(os.path.join(app.static_folder, 'uploads', 'duty_leave'), exist_ok=True)

from database.schema_init import init_all_tables
init_all_tables()

@app.route('/dashboard')
def dashboard():
    """Redirect to the role-specific dashboard if authenticated."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for(f"{session['role']}_dashboard"))

from utils.helpers import get_advisor_details, get_active_device, get_session_info, update_session_state, get_device_command, get_student_details, get_student_attendance, get_teacher_details, get_teacher_dashboard_data

@app.route('/student/dashboard')
def student_dashboard():
    """Render the student dashboard if authorized."""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or role != 'student':
        return redirect(url_for('login'))
        
    student = get_student_details(user_id)
    device_info = get_active_device()
    
    if not student:
        return "Student profile not found. Please contact an admin.", 404
        
    subjects_data = get_student_attendance(student['student_id'])
    
    # Calculate overall stats
    total_conducted = sum(s['conducted'] for s in subjects_data)
    total_attended = sum(s['attended'] for s in subjects_data)
    total_absent = total_conducted - total_attended
    overall_percentage = round((total_attended / total_conducted * 100) if total_conducted > 0 else 0)
    
    return render_template('dashboard.html', 
                           student=student, 
                           device_info=device_info, 
                           subjects=subjects_data,
                           total_conducted=total_conducted,
                           total_attended=total_attended,
                           total_absent=total_absent,
                           overall_percentage=overall_percentage)



@app.route('/advisor/dashboard')
def advisor_dashboard():
    """Render the advisor dashboard if authorized."""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or role != 'advisor':
        return redirect(url_for('login'))
        
    advisor = get_advisor_details(user_id)
    device_info = get_active_device()
    session_info = get_session_info()
    
    if not advisor:
        # Fallback if profile is missing - you might want to redirect or show an error
        return "Advisor profile not found. Please contact the administrator.", 404
        
    return render_template('advisor_dashboard.html', 
                         advisor=advisor, 
                         device_info=device_info,
                         session_info=session_info)

# --- Session Control APIs ---

@app.route('/api/session/start', methods=['POST'])
def api_start_session():
    """Start an attendance session and dispatch camera command."""
    if 'user_id' not in session or session.get('role') != 'advisor':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    device_info = get_active_device()
    if device_info['status'] != 'Connected':
        return jsonify({"success": False, "message": "No active device connected"}), 400
        
    if update_session_state("active"):
        return jsonify({"success": True, "message": "Session started and command dispatched"})
    return jsonify({"success": False, "message": "Failed to update session state"}), 500

@app.route('/api/session/stop', methods=['POST'])
def api_stop_session():
    """Stop the current attendance session and dispatch camera command."""
    if 'user_id' not in session or session.get('role') != 'advisor':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    if update_session_state("stopped"):
        return jsonify({"success": True, "message": "Session stopped and command dispatched"})
    return jsonify({"success": False, "message": "Failed to update session state"}), 500

# --- Device Polling API ---

@app.route('/api/device/command/<device_id>', methods=['GET'])
def api_get_device_command(device_id):
    """Endpoint for Raspberry Pi to poll for commands."""
    # In production, add API key validation here
    command_info = get_device_command(device_id)
    return jsonify({
        "device_id": device_id,
        "command": command_info["command"],
        "timestamp": command_info["updated_at"]
    })

@app.route('/advisor/manage')
def advisor_manage():
    """Render the advisor manage page with dynamic data."""
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'advisor':
        return redirect(url_for('login'))
        
    subject_code = request.args.get('subject')
    from utils.helpers import get_advisor_manage_data, get_active_device
    
    data = get_advisor_manage_data(user_id, subject_code)
    device_info = get_active_device()
    
    if not data:
        # Fallback if no data found for advisor/batch
        return redirect(url_for('advisor_dashboard'))
        
    return render_template('advisor_manage.html', data=data, device_info=device_info)


@app.route('/teacher/dashboard')
def teacher_dashboard():
    """Render the teacher dashboard if authorized."""
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'teacher':
        return redirect(url_for('login'))
        
    device_info = get_active_device()
    teacher = get_teacher_details(user_id)
    dashboard_data = get_teacher_dashboard_data(user_id)
    
    if not teacher:
        return "Teacher profile not found. Please contact the administrator.", 404
        
    return render_template('teacher_dashboard.html',
                         device_info=device_info,
                         teacher=teacher,
                         dashboard_data=dashboard_data)


@app.route('/teacher/subject/manage/<subject_code>')
def teacher_subject_manage(subject_code):
    """Render the teacher's subject manage page."""
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    teacher = get_teacher_details(user_id)
    device_info = get_active_device()
    
    from utils.helpers import get_subject_manage_data
    manage_data = get_subject_manage_data(subject_code)
    
    if not manage_data:
        # If no data found for this subject, redirect back to dashboard
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('teacher_subject_manage.html', 
                          teacher=teacher, 
                          device_info=device_info,
                          data=manage_data)

@app.route('/teacher/manage')
def teacher_manage():
    """Smart redirect to the first subject handled by the teacher."""
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    
    from utils.helpers import get_teacher_dashboard_data
    dashboard_data = get_teacher_dashboard_data(user_id)
    
    if dashboard_data['subjects']:
        # Redirect to the first handled subject
        first_subject = dashboard_data['subjects'][0]['short_code']
        return redirect(url_for('teacher_subject_manage', subject_code=first_subject))
    
    # Fallback to dashboard if no subjects found
    return redirect(url_for('teacher_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Render the admin dashboard if authorized."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', username=session.get('username'), role=session.get('role'))


@app.route('/')
def login():
    """Render the login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
