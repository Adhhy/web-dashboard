from flask import Flask, render_template, session, redirect, url_for
from config import Config
from auth.auth_handler import auth_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp)

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

@app.route('/advisor/dashboard')
def advisor_dashboard():
    """Render the advisor dashboard if authorized."""
    if 'user_id' not in session or session.get('role') != 'advisor':
        return redirect(url_for('login'))
    return render_template('dashboard.html')

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
