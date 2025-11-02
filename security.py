"""
Security middleware for ReconX
Provides additional security features and validation
"""

from functools import wraps
from flask import request, jsonify, current_app
import re
import logging

logger = logging.getLogger(__name__)

def validate_input(data, required_fields=None, allowed_fields=None):
    """Validate input data for security"""
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    # Check required fields
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
    
    # Check allowed fields (whitelist)
    if allowed_fields:
        invalid_fields = [field for field in data.keys() if field not in allowed_fields]
        if invalid_fields:
            return False, f"Invalid fields: {invalid_fields}"
    
    return True, "Valid"

def sanitize_string(value, max_length=1000):
    """Sanitize string input to prevent injection attacks"""
    if not isinstance(value, str):
        return str(value)
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>"\']', '', value)
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()

def validate_filename(filename):
    """Validate filename for security"""
    if not filename:
        return False, "Filename is required"
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename: path traversal detected"
    
    # Check file extension
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'csv', 'xlsx', 'xls'})
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        return False, f"Invalid file extension: {ext}"
    
    return True, "Valid filename"

def require_https():
    """Decorator to require HTTPS in production"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_app.debug and not request.is_secure:
                return jsonify({
                    'error': 'HTTPS Required',
                    'message': 'This endpoint requires HTTPS'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_file_size(file_size, max_size_mb=50):
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    return True, "Valid file size"

def log_security_event(event_type, details, ip_address=None):
    """Log security-related events"""
    try:
        from ..database import audit_manager
        audit_manager.log_action(
            user_id=None,
            action=f"security_{event_type}",
            details=details,
            ip_address=ip_address or request.remote_addr
        )
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")

def check_suspicious_activity(ip_address, user_id=None):
    """Check for suspicious activity patterns"""
    # This is a simplified version - in production, you'd want more sophisticated detection
    try:
        from ..database import audit_manager
        
        # Get recent failed login attempts
        recent_logs = audit_manager.get_audit_logs(limit=100)
        failed_attempts = [
            log for log in recent_logs 
            if log.get('action') == 'login_failed' 
            and log.get('ip_address') == ip_address
        ]
        
        if len(failed_attempts) >= 5:  # 5 failed attempts
            log_security_event("suspicious_activity", {
                "type": "multiple_failed_logins",
                "ip_address": ip_address,
                "attempts": len(failed_attempts)
            }, ip_address)
            return True, "Multiple failed login attempts detected"
        
        return False, "No suspicious activity"
        
    except Exception as e:
        logger.error(f"Failed to check suspicious activity: {e}")
        return False, "Check failed"

def validate_json_payload():
    """Decorator to validate JSON payload"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                if not request.is_json:
                    return jsonify({
                        'error': 'Invalid Content-Type',
                        'message': 'Content-Type must be application/json'
                    }), 400
                
                try:
                    data = request.get_json()
                    if data is None:
                        return jsonify({
                            'error': 'Invalid JSON',
                            'message': 'Request body must contain valid JSON'
                        }), 400
                except Exception as e:
                    return jsonify({
                        'error': 'Invalid JSON',
                        'message': f'Failed to parse JSON: {str(e)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator
