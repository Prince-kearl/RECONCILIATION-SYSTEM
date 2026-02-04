from functools import wraps
from flask import request, jsonify, current_app
import jwt
try:
    from ..database import user_manager
except ImportError:
    from database import user_manager

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        try:
            token = token[7:]
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            user = user_manager.get_user_by_id(payload['user_id'])
            if not user:
                return jsonify({'error': 'Invalid user'}), 401
            request.current_user = user
        except Exception as e:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated
