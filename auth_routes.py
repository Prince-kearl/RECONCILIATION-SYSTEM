"""
ReconX Authentication API Routes
Handles login, logout, MFA, and token management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime

from services.auth_service import auth_service, mfa_service, password_service
from services.authorization_service import authorization_service
from middleware.auth_middleware import require_auth, rate_limit_auth
from utils.api_responses import APIResponse
from utils.security import validate_email, validate_username
from utils.logger import get_logger, security_logger
from database import user_manager, audit_manager

logger = get_logger('auth_routes')

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@rate_limit_auth(max_attempts=5, window_seconds=300)
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Request data required")
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return APIResponse.error("Username and password are required")
        
        # Authenticate user
        success, user, message = auth_service.authenticate_user(
            username=username,
            password=password,
            ip_address=request.remote_addr
        )
        
        if not success:
            return APIResponse.error(message, "AUTHENTICATION_FAILED")
        
        # Check if MFA setup is required
        if message == "MFA setup required":
            return APIResponse.success(
                data={
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'mfa_required': True,
                    'mfa_enabled': False
                },
                message="MFA setup required"
            )
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user)
        
        # Create user session
        session_id = auth_service.create_user_session(
            user_id=user['user_id'],
            token_hash=tokens['access_token'][:32],  # Use first 32 chars as hash
            ip_address=request.remote_addr
        )
        
        # Log successful login
        audit_manager.log_action(
            user_id=user['user_id'],
            action='user_login',
            resource_type='auth',
            resource_id='login',
            details={
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'session_id': session_id
            }
        )
        
        return APIResponse.success(
            data={
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'role_name': user.get('role_name', ''),
                    'mfa_enabled': user.get('mfa_enabled', False),
                    'mfa_required': user.get('mfa_required', False)
                },
                'tokens': tokens,
                'session_id': session_id
            },
            message="Login successful"
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return APIResponse.server_error("Login service error")

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    try:
        user_id = request.current_user.get('user_id')
        
        # Invalidate all sessions for user
        auth_service.invalidate_all_user_sessions(user_id)
        
        # Log logout
        audit_manager.log_action(
            user_id=user_id,
            action='user_logout',
            resource_type='auth',
            resource_id='logout',
            details={
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
        )
        
        return APIResponse.success(message="Logout successful")
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return APIResponse.server_error("Logout service error")

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Request data required")
        
        refresh_token = data.get('refresh_token', '')
        if not refresh_token:
            return APIResponse.error("Refresh token required")
        
        # Refresh token
        success, tokens, error = auth_service.refresh_access_token(refresh_token)
        if not success:
            return APIResponse.unauthorized(f"Token refresh failed: {error}")
        
        return APIResponse.success(
            data={'tokens': tokens},
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return APIResponse.server_error("Token refresh service error")

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    try:
        user_id = request.current_user.get('user_id')
        
        # Get fresh user data
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return APIResponse.error("User not found", "USER_NOT_FOUND")
        
        # Get role information
        role_info = authorization_service.get_user_role_info(user_id)
        
        return APIResponse.success(
            data={
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'role_name': user.get('role_name', ''),
                    'status': user.get('status', ''),
                    'mfa_enabled': user.get('mfa_enabled', False),
                    'mfa_required': user.get('mfa_required', False),
                    'last_login': user.get('last_login'),
                    'created_at': user.get('created_at')
                },
                'role': role_info
            },
            message="User information retrieved"
        )
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return APIResponse.server_error("User information service error")

@auth_bp.route('/mfa/setup', methods=['POST'])
@require_auth
def setup_mfa():
    """Setup MFA for user"""
    try:
        user_id = request.current_user.get('user_id')
        
        # Check if MFA is already enabled
        user = user_manager.get_user_by_id(user_id)
        if user.get('mfa_enabled'):
            return APIResponse.error("MFA is already enabled", "MFA_ALREADY_ENABLED")
        
        # Generate MFA secret
        mfa_data = mfa_service.generate_mfa_secret(
            user_id=user_id,
            username=user['username']
        )
        
        # Log MFA setup initiation
        audit_manager.log_action(
            user_id=user_id,
            action='mfa_setup_initiated',
            resource_type='auth',
            resource_id='mfa_setup',
            details={'ip_address': request.remote_addr}
        )
        
        return APIResponse.success(
            data={
                'secret': mfa_data['secret'],
                'backup_codes': mfa_data['backup_codes'],
                'qr_code_uri': mfa_data['qr_code_uri']
            },
            message="MFA setup initiated"
        )
        
    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        return APIResponse.server_error("MFA setup service error")

@auth_bp.route('/mfa/verify', methods=['POST'])
@require_auth
def verify_mfa():
    """Verify MFA code and complete setup"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Request data required")
        
        user_id = request.current_user.get('user_id')
        code = data.get('code', '').strip()
        
        if not code:
            return APIResponse.error("MFA code required")
        
        # Verify MFA code
        success, error = mfa_service.verify_mfa_code(user_id, code)
        if not success:
            return APIResponse.error(f"MFA verification failed: {error}", "MFA_VERIFICATION_FAILED")
        
        # Enable MFA for user
        mfa_service.enable_mfa(user_id)
        
        # Log MFA setup completion
        audit_manager.log_action(
            user_id=user_id,
            action='mfa_setup_completed',
            resource_type='auth',
            resource_id='mfa_setup',
            details={'ip_address': request.remote_addr}
        )
        
        return APIResponse.success(message="MFA setup completed successfully")
        
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        return APIResponse.server_error("MFA verification service error")

@auth_bp.route('/mfa/disable', methods=['POST'])
@require_auth
def disable_mfa():
    """Disable MFA for user"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Request data required")
        
        user_id = request.current_user.get('user_id')
        password = data.get('password', '')
        
        if not password:
            return APIResponse.error("Password required to disable MFA")
        
        # Verify password
        user = user_manager.get_user_by_id(user_id)
        if not password_service.verify_password(password, user['password_hash']):
            return APIResponse.error("Invalid password", "INVALID_PASSWORD")
        
        # Disable MFA
        success = mfa_service.disable_mfa(user_id)
        if not success:
            return APIResponse.error("Failed to disable MFA")
        
        # Log MFA disable
        audit_manager.log_action(
            user_id=user_id,
            action='mfa_disabled',
            resource_type='auth',
            resource_id='mfa_disable',
            details={'ip_address': request.remote_addr}
        )
        
        return APIResponse.success(message="MFA disabled successfully")
        
    except Exception as e:
        logger.error(f"MFA disable error: {e}")
        return APIResponse.server_error("MFA disable service error")

@auth_bp.route('/mfa/verify-login', methods=['POST'])
def verify_mfa_login():
    """Verify MFA code during login"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Request data required")
        
        user_id = data.get('user_id')
        code = data.get('code', '').strip()
        
        if not user_id or not code:
            return APIResponse.error("User ID and MFA code required")
        
        # Verify MFA code
        success, error = mfa_service.verify_mfa_code(user_id, code)
        if not success:
            return APIResponse.error(f"MFA verification failed: {error}", "MFA_VERIFICATION_FAILED")
        
        # Get user data
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return APIResponse.error("User not found")
        
        # Generate tokens
        tokens = auth_service.generate_tokens(user)
        
        # Create user session
        session_id = auth_service.create_user_session(
            user_id=user_id,
            token_hash=tokens['access_token'][:32],
            ip_address=request.remote_addr
        )
        
        # Log successful MFA login
        audit_manager.log_action(
            user_id=user_id,
            action='mfa_login_completed',
            resource_type='auth',
            resource_id='mfa_login',
            details={
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'session_id': session_id
            }
        )
        
        return APIResponse.success(
            data={
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'role_name': user.get('role_name', ''),
                    'mfa_enabled': user.get('mfa_enabled', False),
                    'mfa_required': user.get('mfa_required', False)
                },
                'tokens': tokens,
                'session_id': session_id
            },
            message="MFA login successful"
        )
        
    except Exception as e:
        logger.error(f"MFA login verification error: {e}")
        return APIResponse.server_error("MFA login verification service error")

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Request data required")
        
        user_id = request.current_user.get('user_id')
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return APIResponse.error("Current and new passwords are required")
        
        # Change password
        success, message = password_service.change_password(
            user_id=user_id,
            current_password=current_password,
            new_password=new_password
        )
        
        if not success:
            return APIResponse.error(message, "PASSWORD_CHANGE_FAILED")
        
        return APIResponse.success(message=message)
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return APIResponse.server_error("Password change service error")

@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """Get user's active sessions"""
    try:
        user_id = request.current_user.get('user_id')
        
        # Get user sessions
        sessions = user_manager.get_user_sessions(user_id)
        
        return APIResponse.success(
            data={'sessions': sessions},
            message="User sessions retrieved"
        )
        
    except Exception as e:
        logger.error(f"Get user sessions error: {e}")
        return APIResponse.server_error("Session retrieval service error")

@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def revoke_session(session_id):
    """Revoke a specific user session"""
    try:
        user_id = request.current_user.get('user_id')
        
        # Revoke session
        success = auth_service.invalidate_session(session_id)
        if not success:
            return APIResponse.error("Failed to revoke session")
        
        # Log session revocation
        audit_manager.log_action(
            user_id=user_id,
            action='session_revoked',
            resource_type='auth',
            resource_id=f'session_{session_id}',
            details={'ip_address': request.remote_addr}
        )
        
        return APIResponse.success(message="Session revoked successfully")
        
    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        return APIResponse.server_error("Session revocation service error")

@auth_bp.route('/sessions/revoke-all', methods=['POST'])
@require_auth
def revoke_all_sessions():
    """Revoke all user sessions except current"""
    try:
        user_id = request.current_user.get('user_id')
        
        # Revoke all sessions
        success = auth_service.invalidate_all_user_sessions(user_id)
        if not success:
            return APIResponse.error("Failed to revoke sessions")
        
        # Log session revocation
        audit_manager.log_action(
            user_id=user_id,
            action='all_sessions_revoked',
            resource_type='auth',
            resource_id='sessions',
            details={'ip_address': request.remote_addr}
        )
        
        return APIResponse.success(message="All sessions revoked successfully")
        
    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        return APIResponse.server_error("Session revocation service error")

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Authentication service health check"""
    try:
        return APIResponse.success(
            data={
                'service': 'authentication',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat()
            },
            message="Authentication service is healthy"
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return APIResponse.server_error("Health check failed")
