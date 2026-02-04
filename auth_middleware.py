"""
ReconX Authentication Middleware
JWT token validation and user context management
"""

import time
from functools import wraps
from typing import Optional, Dict, Any
from flask import request, jsonify, current_app, g

from services.auth_service import auth_service
from services.authorization_service import authorization_service
from utils.logger import get_logger, security_logger
from utils.api_responses import APIResponse

logger = get_logger('auth_middleware')

class AuthenticationMiddleware:
    """Middleware for JWT authentication and user context"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        self.app = app
        
        # Register before_request handler
        app.before_request(self.before_request)
        
        # Register after_request handler
        app.after_request(self.after_request)
        
        # Register error handlers
        app.register_error_handler(401, self.handle_unauthorized)
        app.register_error_handler(403, self.handle_forbidden)
    
    def before_request(self):
        """Process request before it reaches the route"""
        try:
            # Skip authentication for certain endpoints
            if self._should_skip_auth():
                return None
            
            # Get token from request
            token = self._extract_token()
            if not token:
                return APIResponse.unauthorized("Authentication token required")
            
            # Verify token
            valid, payload, error = auth_service.verify_token(token)
            if not valid:
                security_logger.log_suspicious_activity(
                    'invalid_token',
                    f'Invalid token attempt: {error}',
                    ip_address=request.remote_addr
                )
                return APIResponse.unauthorized(f"Invalid token: {error}")
            
            # Set user context
            request.current_user = payload
            
            # Check if MFA is required but not completed
            if self._requires_mfa_completion(payload):
                return APIResponse.unauthorized("MFA verification required")
            
            # Log successful authentication
            logger.debug(f"User {payload.get('user_id')} authenticated for {request.endpoint}")
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return APIResponse.server_error("Authentication service error")
    
    def after_request(self, response):
        """Process response after route execution"""
        try:
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Add user context to response headers for debugging
            if hasattr(request, 'current_user') and request.current_user:
                user_id = request.current_user.get('user_id')
                if user_id:
                    response.headers['X-User-ID'] = str(user_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Response middleware error: {e}")
            return response
    
    def _should_skip_auth(self) -> bool:
        """Check if authentication should be skipped for this endpoint"""
        skip_endpoints = {
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/refresh',
            '/api/auth/mfa/setup',
            '/api/auth/mfa/verify',
            '/api/health',
            '/api/docs',
            '/static/',
            '/favicon.ico'
        }
        
        path = request.path
        return any(path.startswith(endpoint) for endpoint in skip_endpoints)
    
    def _extract_token(self) -> Optional[str]:
        """Extract JWT token from request"""
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # Check X-Auth-Token header
        token_header = request.headers.get('X-Auth-Token')
        if token_header:
            return token_header
        
        # Check query parameter (for testing only)
        if current_app.config.get('TESTING'):
            token_param = request.args.get('token')
            if token_param:
                return token_param
        
        return None
    
    def _requires_mfa_completion(self, payload: Dict[str, Any]) -> bool:
        """Check if MFA completion is required"""
        # Skip MFA check for MFA-related endpoints
        if request.path.startswith('/api/auth/mfa/'):
            return False
        
        # Check if user has MFA enabled and required
        mfa_enabled = payload.get('mfa_enabled', False)
        mfa_required = payload.get('mfa_required', False)
        
        # If MFA is required but not enabled, block access
        if mfa_required and not mfa_enabled:
            return True
        
        return False
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return APIResponse.unauthorized("Authentication required")
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return APIResponse.forbidden("Access denied")

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user:
            return APIResponse.unauthorized("Authentication required")
        
        user_id = request.current_user.get('user_id')
        if not user_id:
            return APIResponse.unauthorized("Invalid user session")
        
        return f(*args, **kwargs)
    return decorated_function

def require_mfa(f):
    """Decorator to require MFA verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user:
            return APIResponse.unauthorized("Authentication required")
        
        user_id = request.current_user.get('user_id')
        if not user_id:
            return APIResponse.unauthorized("Invalid user session")
        
        # Check MFA status
        mfa_enabled = request.current_user.get('mfa_enabled', False)
        mfa_required = request.current_user.get('mfa_required', False)
        
        if mfa_required and not mfa_enabled:
            return APIResponse.unauthorized("MFA setup required")
        
        return f(*args, **kwargs)
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to authenticate if token is provided
        if not hasattr(request, 'current_user'):
            token = _extract_token_static()
            if token:
                valid, payload, error = auth_service.verify_token(token)
                if valid:
                    request.current_user = payload
        
        return f(*args, **kwargs)
    return decorated_function

def _extract_token_static() -> Optional[str]:
    """Static method to extract token (for decorators)"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    token_header = request.headers.get('X-Auth-Token')
    if token_header:
        return token_header
    
    return None

# Rate limiting middleware integration
def rate_limit_auth(max_attempts: int, window_seconds: int = 300):
    """Rate limiting decorator for authentication endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as key for rate limiting
            key = request.remote_addr
            
            # Check rate limit
            from utils.security import rate_limiter
            allowed, lockout_remaining = rate_limiter.is_allowed(key, max_attempts, window_seconds)
            
            if not allowed:
                security_logger.log_suspicious_activity(
                    'auth_rate_limit_exceeded',
                    f'Authentication rate limit exceeded for {key}',
                    ip_address=key
                )
                
                return APIResponse.rate_limited(
                    f"Too many authentication attempts. Try again in {int(lockout_remaining)} seconds.",
                    int(lockout_remaining)
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Session management
def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    return getattr(request, 'current_user', None)

def get_current_user_id() -> Optional[int]:
    """Get current user ID"""
    user = get_current_user()
    return user.get('user_id') if user else None

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return hasattr(request, 'current_user') and request.current_user is not None

def logout_user():
    """Logout current user by clearing session"""
    if hasattr(request, 'current_user') and request.current_user:
        user_id = request.current_user.get('user_id')
        if user_id:
            # Invalidate all sessions for user
            auth_service.invalidate_all_user_sessions(user_id)
            
            # Log logout
            security_logger.log_suspicious_activity(
                'user_logout',
                f'User {user_id} logged out',
                user_id=user_id,
                ip_address=request.remote_addr
            )
    
    # Clear user context
    if hasattr(request, 'current_user'):
        delattr(request, 'current_user')

# Global middleware instance
auth_middleware = AuthenticationMiddleware()
