"""
ReconX Security Utilities
Security functions, rate limiting, and input validation
"""

import re
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from config import config
from utils.logger import security_logger

class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self.attempts: Dict[str, List[float]] = {}
        self.lockouts: Dict[str, float] = {}
    
    def is_allowed(self, key: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int]:
        """Check if request is allowed"""
        now = time.time()
        
        # Check if account is locked out
        if key in self.lockouts:
            if now < self.lockouts[key]:
                return False, int(self.lockouts[key] - now)
            else:
                del self.lockouts[key]
        
        # Initialize attempts list
        if key not in self.attempts:
            self.attempts[key] = []
        
        # Remove old attempts outside the window
        self.attempts[key] = [attempt for attempt in self.attempts[key] 
                             if now - attempt < window_seconds]
        
        # Check if limit exceeded
        if len(self.attempts[key]) >= max_attempts:
            # Lock out for specified duration
            lockout_duration = config.LOGIN_LOCKOUT_DURATION * 60  # Convert to seconds
            self.lockouts[key] = now + lockout_duration
            return False, lockout_duration
        
        # Add current attempt
        self.attempts[key].append(now)
        return True, 0
    
    def get_remaining_attempts(self, key: str, max_attempts: int) -> int:
        """Get remaining attempts for a key"""
        if key not in self.attempts:
            return max_attempts
        return max(0, max_attempts - len(self.attempts[key]))

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_attempts: int, window_seconds: int = 300):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as key
            key = request.remote_addr
            
            allowed, lockout_remaining = rate_limiter.is_allowed(key, max_attempts, window_seconds)
            
            if not allowed:
                security_logger.log_suspicious_activity(
                    'rate_limit_exceeded',
                    f'Rate limit exceeded for {key}',
                    ip_address=key
                )
                
                return jsonify({
                    'success': False,
                    'message': f'Too many requests. Try again in {int(lockout_remaining)} seconds.',
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_password(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength"""
    errors = []
    
    if len(password) < config.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_file_upload(filename: str, file_size: int) -> Tuple[bool, List[str]]:
    """Validate file upload"""
    errors = []
    
    # Check file extension
    if '.' not in filename:
        errors.append("File must have an extension")
    else:
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in config.ALLOWED_EXTENSIONS:
            errors.append(f"File type .{extension} is not allowed. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}")
    
    # Check file size
    if file_size > config.MAX_CONTENT_LENGTH:
        max_size_mb = config.MAX_CONTENT_LENGTH / (1024 * 1024)
        errors.append(f"File size exceeds maximum allowed size of {max_size_mb}MB")
    
    # Check filename length
    if len(filename) > 255:
        errors.append("Filename is too long")
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'\.\./',  # Directory traversal
        r'\.\.\\',  # Windows directory traversal
        r'\.exe$',  # Executable files
        r'\.bat$',  # Batch files
        r'\.cmd$',  # Command files
        r'\.com$',  # Command files
        r'\.pif$',  # Program information files
        r'\.scr$',  # Screen saver files
        r'\.vbs$',  # VBScript files
        r'\.js$',   # JavaScript files
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            errors.append("Filename contains suspicious patterns")
            break
    
    return len(errors) == 0, errors

def generate_secure_filename(original_filename: str, prefix: str = "") -> str:
    """Generate a secure filename"""
    import uuid
    
    # Get file extension
    if '.' in original_filename:
        extension = original_filename.rsplit('.', 1)[1].lower()
    else:
        extension = ''
    
    # Generate unique filename
    unique_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    
    if prefix:
        secure_filename = f"{prefix}_{timestamp}_{unique_id}"
    else:
        secure_filename = f"{timestamp}_{unique_id}"
    
    if extension:
        secure_filename += f".{extension}"
    
    return secure_filename

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging (not for passwords)"""
    return hashlib.sha256(data.encode()).hexdigest()[:8]

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> Tuple[bool, List[str]]:
    """Validate username format"""
    errors = []
    
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    if len(username) > 50:
        errors.append("Username must be less than 50 characters long")
    
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        errors.append("Username can only contain letters, numbers, dots, underscores, and hyphens")
    
    if username.startswith('.') or username.endswith('.'):
        errors.append("Username cannot start or end with a dot")
    
    if username.startswith('-') or username.endswith('-'):
        errors.append("Username cannot start or end with a hyphen")
    
    return len(errors) == 0, errors

def sanitize_sql_input(text: str) -> str:
    """Basic SQL injection prevention (use parameterized queries instead)"""
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_"]
    
    for char in dangerous_chars:
        if char in text.lower():
            security_logger.log_suspicious_activity(
                'sql_injection_attempt',
                f'Potential SQL injection attempt: {hash_sensitive_data(text)}',
                ip_address=request.remote_addr if request else None
            )
            raise ValueError("Input contains potentially dangerous characters")
    
    return text

def validate_reconciliation_config(tolerance: float, batch_size: int) -> Tuple[bool, List[str]]:
    """Validate reconciliation configuration parameters"""
    errors = []
    
    if tolerance < 0:
        errors.append("Tolerance cannot be negative")
    
    if tolerance > 1000000:  # 1 million
        errors.append("Tolerance is unreasonably high")
    
    if batch_size < 1:
        errors.append("Batch size must be at least 1")
    
    if batch_size > 10000:  # 10k
        errors.append("Batch size cannot exceed 10,000")
    
    return len(errors) == 0, errors

# Security decorators
def require_https(f):
    """Require HTTPS in production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not config.DEBUG:
            return jsonify({
                'success': False,
                'message': 'HTTPS required in production',
                'error_code': 'HTTPS_REQUIRED'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_json_schema(schema: Dict):
    """Validate JSON request schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Request must be JSON',
                    'error_code': 'INVALID_CONTENT_TYPE'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON data',
                    'error_code': 'INVALID_JSON'
                }), 400
            
            # Basic schema validation
            for field, field_type in schema.items():
                if field not in data:
                    return jsonify({
                        'success': False,
                        'message': f'Missing required field: {field}',
                        'error_code': 'MISSING_FIELD'
                    }), 400
                
                if not isinstance(data[field], field_type):
                    return jsonify({
                        'success': False,
                        'message': f'Invalid type for field {field}',
                        'error_code': 'INVALID_TYPE'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
