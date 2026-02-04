from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import jwt
import logging

try:
    from ..services.user_service import UserService
    from ..database import audit_manager
except ImportError:
    from services.user_service import UserService
    from database import audit_manager

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

user_service = UserService()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        u = user_service.get_by_username(username)
        user = None
        if u:
            user = {
                'user_id': u.user_id,
                'username': u.username,
                'password_hash': u.password_hash,
                'full_name': u.full_name,
                'email': u.email,
                'role_id': u.role_id,
                'role_name': u.role_name,
                'status': u.status,
            }
        valid_password = False
        if user and isinstance(user.get('password_hash'), str):
            stored_hash = user['password_hash']
            try:
                # support werkzeug hashes and bcrypt ($2b$...)
                if stored_hash.startswith('$2b$'):
                    import bcrypt
                    valid_password = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
                else:
                    valid_password = check_password_hash(stored_hash, password)
            except Exception:
                valid_password = False

        if not user or not valid_password:
            try:
                audit_manager.log_action(user_id=None, action='login_failed', details=None, ip_address=request.remote_addr)
            except Exception:
                pass
            return jsonify({'error': 'Invalid credentials'}), 401

        if user.get('status') != 'active':
            return jsonify({'error': 'Account is not active'}), 401

        # Update last login
        try:
            try:
                from ..database import user_manager
            except ImportError:
                from database import user_manager
            user_manager.update_last_login(user['user_id'])
        except Exception:
            pass

        # Build JWT with explicit exp timestamp for PyJWT 2.x compatibility
        ttl = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
        try:
            # Support both timedelta and numeric hours
            if isinstance(ttl, int):
                exp_dt = datetime.utcnow() + timedelta(hours=ttl)
            else:
                exp_dt = datetime.utcnow() + ttl
        except Exception:
            exp_dt = datetime.utcnow() + timedelta(hours=8)

        payload = {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user.get('role_name'),
            'exp': exp_dt
        }

        try:
            token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        except Exception as e:
            logger.error(f"JWT encode failed: {e}")
            return jsonify({'error': 'Login failed'}), 500

        try:
            audit_manager.log_action(user_id=user['user_id'], action='login_success', details=None, ip_address=request.remote_addr)
        except Exception:
            pass

        return jsonify({'token': token, 'user': {
            'id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'role': user.get('role_name'),
            'full_name': user.get('full_name')
        }})
    except Exception as e:
        logger.exception(f"Login error: {e}")
        if current_app.config.get('DEBUG'):
            return jsonify({'error': 'Login failed', 'detail': str(e)}), 500
        return jsonify({'error': 'Login failed'}), 500


