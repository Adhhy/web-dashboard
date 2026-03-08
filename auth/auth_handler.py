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
