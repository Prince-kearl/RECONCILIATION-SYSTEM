"""
ReconX Authentication Service
Handles JWT authentication, MFA, password management, and user sessions
"""

import jwt
import pyotp
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request

from config import config
from utils.logger import security_logger, get_logger
from utils.security import validate_password, validate_email, validate_username
from database import user_manager, audit_manager

logger = get_logger('auth_service')

class AuthenticationService:
    """Main authentication service for ReconX"""
    
    def __init__(self):
        self.jwt_secret = config.JWT_SECRET_KEY
        self.access_token_expires = config.JWT_ACCESS_TOKEN_EXPIRES
        self.refresh_token_expires = config.JWT_REFRESH_TOKEN_EXPIRES
    
    def authenticate_user(self, username: str, password: str, ip_address: str) -> Tuple[bool, Dict, str]:
        """
        Authenticate user with username and password
        
        Returns:
            Tuple[bool, Dict, str]: (success, user_data, error_message)
        """
        try:
            # Get user from database
            user = user_manager.get_user_by_username(username)
            if not user:
                security_logger.log_failed_login(username, ip_address, "User not found")
                return False, {}, "Invalid username or password"
            
            # Check if account is locked
            if user.get('status') == 'locked':
                if user.get('account_locked_until'):
                    lockout_time = user['account_locked_until']
                    if datetime.now() < lockout_time:
                        remaining_time = int((lockout_time - datetime.now()).total_seconds())
                        security_logger.log_failed_login(username, ip_address, "Account locked")
                        return False, {}, f"Account is locked. Try again in {remaining_time} seconds"
                    else:
                        # Unlock account
                        user_manager.update_user_status(user['user_id'], 'active')
                        user_manager.reset_failed_login_attempts(user['user_id'])
            
            # Check if account is inactive
            if user.get('status') != 'active':
                security_logger.log_failed_login(username, ip_address, f"Account status: {user.get('status')}")
                return False, {}, "Account is not active"
            
            # Verify password
            if not check_password_hash(user['password_hash'], password):
                # Increment failed login attempts
                failed_attempts = user.get('failed_login_attempts', 0) + 1
                user_manager.update_failed_login_attempts(user['user_id'], failed_attempts)
                
                # Check if account should be locked
                if failed_attempts >= config.LOGIN_MAX_ATTEMPTS:
                    lockout_until = datetime.now() + timedelta(minutes=config.LOGIN_LOCKOUT_DURATION)
                    user_manager.lock_account(user['user_id'], lockout_until)
                    security_logger.log_failed_login(username, ip_address, "Account locked due to too many failed attempts")
                    return False, {}, f"Too many failed attempts. Account locked for {config.LOGIN_LOCKOUT_DURATION} minutes"
                
                security_logger.log_failed_login(username, ip_address, "Invalid password")
                remaining_attempts = config.LOGIN_MAX_ATTEMPTS - failed_attempts
                return False, {}, f"Invalid password. {remaining_attempts} attempts remaining"
            
            # Reset failed login attempts on successful login
            user_manager.reset_failed_login_attempts(user['user_id'])
            
            # Update last login
            user_manager.update_last_login(user['user_id'])
            
            # Log successful login
            security_logger.log_login_attempt(username, True, ip_address, user_id=user['user_id'])
            
            # Check if MFA is required
            if user.get('mfa_required') and not user.get('mfa_enabled'):
                return True, user, "MFA setup required"
            
            return True, user, ""
            
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return False, {}, "Authentication service error"
    
    def generate_tokens(self, user: Dict) -> Dict[str, str]:
        """Generate JWT access and refresh tokens"""
        try:
            now = datetime.utcnow()
            
            # Access token payload
            access_payload = {
                'user_id': user['user_id'],
                'username': user['username'],
                'role_id': user['role_id'],
                'role_name': user.get('role_name', ''),
                'mfa_enabled': user.get('mfa_enabled', False),
                'mfa_required': user.get('mfa_required', False),
                'exp': now + timedelta(hours=self.access_token_expires),
                'iat': now,
                'type': 'access'
            }
            
            # Refresh token payload
            refresh_payload = {
                'user_id': user['user_id'],
                'username': user['username'],
                'exp': now + timedelta(days=self.refresh_token_expires),
                'iat': now,
                'type': 'refresh'
            }
            
            # Generate tokens
            access_token = jwt.encode(access_payload, self.jwt_secret, algorithm='HS256')
            refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm='HS256')
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': self.access_token_expires * 3600,  # seconds
                'refresh_expires_in': self.refresh_token_expires * 86400  # seconds
            }
            
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = 'access') -> Tuple[bool, Dict, str]:
        """
        Verify JWT token and return user data
        
        Returns:
            Tuple[bool, Dict, str]: (valid, payload, error_message)
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != token_type:
                return False, {}, "Invalid token type"
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload['exp']:
                return False, {}, "Token expired"
            
            # Get fresh user data
            user = user_manager.get_user_by_id(payload['user_id'])
            if not user or user.get('status') != 'active':
                return False, {}, "User not found or inactive"
            
            # Update payload with fresh user data
            payload.update({
                'role_name': user.get('role_name', ''),
                'mfa_enabled': user.get('mfa_enabled', False),
                'mfa_required': user.get('mfa_required', False)
            })
            
            return True, payload, ""
            
        except jwt.ExpiredSignatureError:
            return False, {}, "Token expired"
        except jwt.InvalidTokenError as e:
            return False, {}, f"Invalid token: {str(e)}"
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, {}, "Token verification error"
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Dict, str]:
        """Generate new access token using refresh token"""
        try:
            # Verify refresh token
            valid, payload, error = self.verify_token(refresh_token, 'refresh')
            if not valid:
                return False, {}, error
            
            # Get fresh user data
            user = user_manager.get_user_by_id(payload['user_id'])
            if not user:
                return False, {}, "User not found"
            
            # Generate new access token
            tokens = self.generate_tokens(user)
            
            return True, tokens, ""
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False, {}, "Token refresh error"
    
    def create_user_session(self, user_id: int, token_hash: str, ip_address: str) -> str:
        """Create user session and return session ID"""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=self.access_token_expires)
            
            # Store session in database
            user_manager.create_user_session(
                session_id=session_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        try:
            return user_manager.invalidate_session(session_id)
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False
    
    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user"""
        try:
            return user_manager.invalidate_all_user_sessions(user_id)
        except Exception as e:
            logger.error(f"User session invalidation error: {e}")
            return False

class MFAService:
    """Multi-Factor Authentication service"""
    
    def __init__(self):
        self.issuer = config.MFA_ISSUER
        self.algorithm = config.MFA_ALGORITHM
        self.digits = config.MFA_DIGITS
        self.period = config.MFA_PERIOD
    
    def generate_mfa_secret(self, user_id: int, username: str) -> Dict[str, str]:
        """Generate MFA secret and QR code data"""
        try:
            # Generate secret key
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
            
            # Store MFA secret
            user_manager.create_mfa_secret(user_id, secret, backup_codes)
            
            # Generate QR code URI
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.period)
            provisioning_uri = totp.provisioning_uri(
                name=username,
                issuer_name=self.issuer
            )
            
            return {
                'secret': secret,
                'backup_codes': backup_codes,
                'qr_code_uri': provisioning_uri
            }
            
        except Exception as e:
            logger.error(f"MFA secret generation error: {e}")
            raise
    
    def verify_mfa_code(self, user_id: int, code: str) -> Tuple[bool, str]:
        """Verify MFA TOTP code"""
        try:
            # Get user's MFA secret
            mfa_secret = user_manager.get_mfa_secret(user_id)
            if not mfa_secret:
                return False, "MFA not configured"
            
            # Check if it's a backup code
            if code in mfa_secret.get('backup_codes', []):
                # Use backup code (remove it after use)
                user_manager.use_backup_code(user_id, code)
                return True, ""
            
            # Verify TOTP code
            totp = pyotp.TOTP(mfa_secret['secret_key'], digits=self.digits, interval=self.period)
            if totp.verify(code):
                return True, ""
            else:
                return False, "Invalid MFA code"
                
        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return False, "MFA verification error"
    
    def enable_mfa(self, user_id: int) -> bool:
        """Enable MFA for user"""
        try:
            return user_manager.enable_mfa(user_id)
        except Exception as e:
            logger.error(f"MFA enable error: {e}")
            return False
    
    def disable_mfa(self, user_id: int) -> bool:
        """Disable MFA for user"""
        try:
            return user_manager.disable_mfa(user_id)
        except Exception as e:
            logger.error(f"MFA disable error: {e}")
            return False

class PasswordService:
    """Password management service"""
    
    def __init__(self):
        self.min_length = config.PASSWORD_MIN_LENGTH
    
    def validate_password_strength(self, password: str) -> Tuple[bool, list]:
        """Validate password meets strength requirements"""
        return validate_password(password)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Get current user
            user = user_manager.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not self.verify_password(current_password, user['password_hash']):
                return False, "Current password is incorrect"
            
            # Validate new password
            is_valid, errors = self.validate_password_strength(new_password)
            if not is_valid:
                return False, f"Password validation failed: {'; '.join(errors)}"
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            success = user_manager.update_password(user_id, new_password_hash)
            if success:
                # Invalidate all sessions to force re-login
                auth_service = AuthenticationService()
                auth_service.invalidate_all_user_sessions(user_id)
                
                # Log password change
                audit_manager.log_action(
                    user_id=user_id,
                    action='password_changed',
                    resource_type='user',
                    resource_id=str(user_id),
                    details={'ip_address': request.remote_addr if request else None}
                )
                
                return True, "Password changed successfully"
            else:
                return False, "Failed to update password"
                
        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False, "Password change error"
    
    def reset_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        """Reset user password (admin function)"""
        try:
            # Validate new password
            is_valid, errors = self.validate_password_strength(new_password)
            if not is_valid:
                return False, f"Password validation failed: {'; '.join(errors)}"
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            success = user_manager.update_password(user_id, new_password_hash)
            if success:
                # Invalidate all sessions
                auth_service = AuthenticationService()
                auth_service.invalidate_all_user_sessions(user_id)
                
                # Log password reset
                audit_manager.log_action(
                    user_id=user_id,
                    action='password_reset',
                    resource_type='user',
                    resource_id=str(user_id),
                    details={'ip_address': request.remote_addr if request else None}
                )
                
                return True, "Password reset successfully"
            else:
                return False, "Failed to reset password"
                
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return False, "Password reset error"

# Global service instances
auth_service = AuthenticationService()
mfa_service = MFAService()
password_service = PasswordService()
