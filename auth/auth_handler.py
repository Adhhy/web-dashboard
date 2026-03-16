from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Handle login authentication requests.
    Expects JSON data: { "username": "...", "password": "..." }
    """
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data or 'role' not in data:
        return jsonify({
            "success": False,
            "message": "Missing username, password, or role."
        }), 400
        
    username = data.get('username')
    password = data.get('password')
    selected_role = data.get('role')
    
    success, message, user_id, role = AuthService.authenticate_user(username, password, selected_role)
    
    if success:
        # Store user information in session
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role
        
        # Determine redirection URL based on role
        if role == 'admin':
            redirect_url = "/admin/dashboard"
        else:
            redirect_url = f"/{role}/dashboard"
        
        return jsonify({
            "success": True,
            "message": message,
            "user_id": user_id,
            "role": role,
            "redirect_url": redirect_url
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": message
        }), 401

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """
    Handle logout requests by clearing the session.
    """
    session.clear()
    return jsonify({
        "success": True,
        "message": "Successfully logged out."
    }), 200

@auth_bp.route('/auth/change-password', methods=['POST'])
def change_password():
    """
    Handle change password requests.
    Expects JSON data: { "current_password": "...", "new_password": "...", "confirm_password": "..." }
    """
    if 'user_id' not in session:
        return jsonify({
            "success": False,
            "message": "Unauthorized. Please log in."
        }), 401

    data = request.get_json()
    
    if not data or 'current_password' not in data or 'new_password' not in data or 'confirm_password' not in data:
        return jsonify({
            "success": False,
            "message": "Missing required fields."
        }), 400
        
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "message": "New password and confirm password do not match."
        }), 400

    user_id = session.get('user_id')
    
    success, message = AuthService.change_password(user_id, current_password, new_password)
    
    if success:
        # Clear the session so they must log in again
        session.clear()
        return jsonify({
            "success": True,
            "message": message
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": message
        }), 400
