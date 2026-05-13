from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

try:
    from ..services import user_service
    from ..database import user_manager, audit_manager
except ImportError:
    from services import user_service
    from database import user_manager, audit_manager

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/', methods=['GET'])
def get_users():
    try:
        users = user_service.get_all()
        return jsonify({'users': users})
    except Exception:
        return jsonify({'error': 'Failed to fetch users'}), 500


@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name') or data.get('fullName') or username
    role_name = data.get('role', 'viewer')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    try:
        roles = {
            'admin': 1,
            'finance_officer': 2,
            'auditor': 3,
            'viewer': 4
        }
        role_id = roles.get(role_name, 4)

        password_hash = generate_password_hash(password)
        user_id = user_manager.create_user(username, password_hash, full_name, email, role_id)

        try:
            audit_manager.log_action(request.current_user['user_id'], 'user_created', None, request.remote_addr)
        except Exception:
            pass

        return jsonify({'success': True, 'user_id': user_id})
    except Exception:
        return jsonify({'error': 'Failed to create user'}), 500


@users_bp.route('/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id: int):
    data = request.get_json() or {}
    status = data.get('status')
    if status not in ['active', 'inactive']:
        return jsonify({'error': 'Invalid status'}), 400
    try:
        success = user_manager.update_user_status(user_id, status)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'User not found'}), 404
    except Exception:
        return jsonify({'error': 'Failed to update user status'}), 500


