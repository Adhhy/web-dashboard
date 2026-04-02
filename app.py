from flask import Flask, render_template, session, redirect, url_for, jsonify
from config import Config
from auth.auth_handler import auth_bp
from attendance import attendance_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp)
app.register_blueprint(attendance_bp)

from routes.system_routes import system_bp
app.register_blueprint(system_bp)

@app.route('/dashboard')
def dashboard():
    """Redirect to the role-specific dashboard if authenticated."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/student/dashboard')
def student_dashboard():
    """Render the student dashboard if authorized."""
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    return render_template('dashboard.html')

from utils.helpers import get_advisor_details, get_active_device, get_session_info, update_session_state, get_device_command

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
    """Render the advisor manage page stub."""
    if 'user_id' not in session or session.get('role') != 'advisor':
        return redirect(url_for('login'))
    return render_template('advisor_manage.html')

@app.route('/advisor/duty_leave')
def advisor_duty_leave():
    """Render the advisor duty leave page stub."""
    if 'user_id' not in session or session.get('role') != 'advisor':
        return redirect(url_for('login'))
    return render_template('advisor_duty_leave.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    """Render the teacher dashboard if authorized."""
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Render the admin dashboard if authorized."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', username=session.get('username'), role=session.get('role'))

@app.route('/admin/dl_management')
def admin_dl_management():
    """Render the DL Management stub for admin users."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dl_management.html')

@app.route('/')
def login():
    """Render the login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
