"""
Routes for viewing system status and sending commands.
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from services.device_service import DeviceService

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return jsonify({'status': 'error', 'error': 'Unauthorized. Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@system_bp.route('/connect', methods=['POST'])
def device_connect():
    """Endpoint for Raspberry Pi to request a connection."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'error': 'Invalid payload data'}), 400
        
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    device_key = data.get('device_key')
    ip_address = data.get('ip_address', request.remote_addr)
    
    if not all([device_id, device_name, device_key]):
        return jsonify({'status': 'error', 'error': 'Missing required fields: device_id, device_name, device_key'}), 400
        
    success = DeviceService.add_device_request(device_id, device_name, device_key, ip_address)
    
    if success:
        return jsonify({'status': 'success', 'message': 'Connection request received and is pending approval'}), 200
    else:
        return jsonify({'status': 'error', 'error': 'Failed to process connection request'}), 500

@system_bp.route('/pending', methods=['GET'])
@admin_required
def get_pending_requests():
    """Admin endpoint to get all pending device connection requests."""
    requests = DeviceService.get_pending_requests()
    return jsonify({'status': 'success', 'requests': requests}), 200

@system_bp.route('/approve', methods=['POST'])
@admin_required
def approve_device():
    """Admin endpoint to approve a pending device connection request."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'error': 'Invalid payload data'}), 400
        
    device_id = data.get('device_id')
    device_key = data.get('device_key')
    
    if not all([device_id, device_key]):
        return jsonify({'status': 'error', 'error': 'Missing required fields: device_id, device_key'}), 400
        
    success = DeviceService.approve_device(device_id, device_key)
    
    if success:
        return jsonify({'status': 'success', 'message': 'Device approved successfully'}), 200
    else:
        return jsonify({'status': 'error', 'error': 'Invalid device key or device not found'}), 400

@system_bp.route('/reject', methods=['POST'])
@admin_required
def reject_device():
    """Admin endpoint to reject a pending device connection request."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'error': 'Invalid payload data'}), 400
        
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'Missing required field: device_id'}), 400
        
    success = DeviceService.reject_device(device_id)
    
    if success:
        return jsonify({'status': 'success', 'message': 'Device request rejected'}), 200
    else:
        return jsonify({'status': 'error', 'error': 'Failed to reject device request'}), 500

@system_bp.route('/devices', methods=['GET'])
@admin_required
def get_devices():
    """Admin endpoint to get all connected devices."""
    devices = DeviceService.get_devices()
    return jsonify({'status': 'success', 'devices': devices}), 200

@system_bp.route('/device/<device_id>', methods=['GET'])
@admin_required
def get_device_info(device_id):
    """Admin endpoint to get information about a specific device."""
    device = DeviceService.get_device_info(device_id)
    print(device)
    if device:
        return jsonify({'status': 'success', 'device': device}), 200
    else:
        return jsonify({'status': 'error', 'error': 'Device not found'}), 404

@system_bp.route('/device-status/<device_id>', methods=['GET', 'POST'])
def get_public_device_status(device_id):
    """Public endpoint for devices to check their own approval status."""
    device_key = None
    if request.method == 'POST':
        data = request.get_json()
        if data:
            device_key = data.get('device_key')
    else:
        device_key = request.args.get('device_key')
        
    if not device_key:
        return jsonify({'status': 'error', 'error': 'Missing device_key'}), 400
        
    result = DeviceService.is_device_approved(device_id, device_key)
    
    if result.get('status') == 'error':
        return jsonify({'status': 'error', 'error': result.get('message')}), 500
        
    return jsonify({'status': 'success', 'result': result}), 200

@system_bp.route('/disconnect', methods=['POST'])
@admin_required
def disconnect_device():
    """Admin endpoint to disconnect a connected device."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'error': 'Invalid payload data'}), 400
        
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'Missing required field: device_id'}), 400
        
    success = DeviceService.disconnect_device(device_id)
    
    if success:
        return jsonify({'status': 'success', 'message': 'Device disconnected'}), 200
    else:
        return jsonify({'status': 'error', 'error': 'Failed to disconnect device'}), 500

@system_bp.route('/device-disconnect', methods=['POST'])
def public_device_disconnect():
    """Public endpoint for devices to disconnect themselves using their key."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'error': 'Invalid payload data'}), 400
        
    device_id = data.get('device_id')
    device_key = data.get('device_key')
    
    if not all([device_id, device_key]):
        return jsonify({'status': 'error', 'error': 'Missing required fields: device_id, device_key'}), 400
        
    success = DeviceService.disconnect_device_with_key(device_id, device_key)
    
    if success:
        return jsonify({'status': 'success', 'message': 'Device disconnected successfully'}), 200
    else:
        return jsonify({'status': 'error', 'error': 'Invalid device key or device not found'}), 401
