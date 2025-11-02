"""
ReconX Authorization Service
Role-Based Access Control (RBAC) implementation
"""

import json
from typing import Dict, List, Optional, Set, Union
from functools import wraps
from flask import request, jsonify, current_app

from config import config
from utils.logger import get_logger, security_logger
from database import user_manager, audit_manager

logger = get_logger('authorization_service')

class Permission:
    """Permission constants"""
    # User permissions
    USER_CREATE = "users:create"
    USER_READ = "users:read"
    USER_UPDATE = "users:update"
    USER_DELETE = "users:delete"
    USER_ACTIVATE = "users:activate"
    USER_DEACTIVATE = "users:deactivate"
    
    # File permissions
    FILE_UPLOAD = "files:upload"
    FILE_READ = "files:read"
    FILE_UPDATE = "files:update"
    FILE_DELETE = "files:delete"
    FILE_PROCESS = "files:process"
    
    # Reconciliation permissions
    RECONCILIATION_CREATE = "reconciliation:create"
    RECONCILIATION_READ = "reconciliation:read"
    RECONCILIATION_UPDATE = "reconciliation:update"
    RECONCILIATION_DELETE = "reconciliation:delete"
    RECONCILIATION_APPROVE = "reconciliation:approve"
    
    # Report permissions
    REPORT_READ = "reports:read"
    REPORT_EXPORT = "reports:export"
    REPORT_CREATE = "reports:create"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    
    # System permissions
    SYSTEM_CONFIGURE = "system:configure"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"

class Role:
    """Role definitions with permissions"""
    
    ROLES = {
        'admin': {
            'name': 'System Administrator',
            'description': 'Full access to all system features',
            'permissions': [
                Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
                Permission.USER_ACTIVATE, Permission.USER_DEACTIVATE,
                Permission.FILE_UPLOAD, Permission.FILE_READ, Permission.FILE_UPDATE, Permission.FILE_DELETE, Permission.FILE_PROCESS,
                Permission.RECONCILIATION_CREATE, Permission.RECONCILIATION_READ, Permission.RECONCILIATION_UPDATE, 
                Permission.RECONCILIATION_DELETE, Permission.RECONCILIATION_APPROVE,
                Permission.REPORT_READ, Permission.REPORT_EXPORT, Permission.REPORT_CREATE,
                Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
                Permission.SYSTEM_CONFIGURE, Permission.SYSTEM_BACKUP, Permission.SYSTEM_RESTORE
            ]
        },
        'finance_officer': {
            'name': 'Finance Officer',
            'description': 'Can upload files and run reconciliation',
            'permissions': [
                Permission.FILE_UPLOAD, Permission.FILE_READ, Permission.FILE_PROCESS,
                Permission.RECONCILIATION_CREATE, Permission.RECONCILIATION_READ,
                Permission.REPORT_READ, Permission.REPORT_EXPORT
            ]
        },
        'auditor': {
            'name': 'Auditor',
            'description': 'Can view reports and audit logs',
            'permissions': [
                Permission.REPORT_READ, Permission.REPORT_EXPORT,
                Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
                Permission.RECONCILIATION_READ
            ]
        },
        'viewer': {
            'name': 'Viewer',
            'description': 'Read-only access to reports',
            'permissions': [
                Permission.REPORT_READ
            ]
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role_name: str) -> List[str]:
        """Get permissions for a specific role"""
        return cls.ROLES.get(role_name, {}).get('permissions', [])
    
    @classmethod
    def get_all_roles(cls) -> Dict[str, Dict]:
        """Get all role definitions"""
        return cls.ROLES
    
    @classmethod
    def role_exists(cls, role_name: str) -> bool:
        """Check if a role exists"""
        return role_name in cls.ROLES

class AuthorizationService:
    """Main authorization service for ReconX"""
    
    def __init__(self):
        self.logger = logger
    
    def get_user_permissions(self, user_id: int) -> Set[str]:
        """Get all permissions for a user based on their role"""
        try:
            user = user_manager.get_user_by_id(user_id)
            if not user:
                return set()
            
            role_name = user.get('role_name', '')
            if not role_name:
                return set()
            
            return set(Role.get_role_permissions(role_name))
            
        except Exception as e:
            self.logger.error(f"Error getting user permissions: {e}")
            return set()
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific permission"""
        try:
            user_permissions = self.get_user_permissions(user_id)
            return permission in user_permissions
            
        except Exception as e:
            self.logger.error(f"Error checking permission: {e}")
            return False
    
    def has_any_permission(self, user_id: int, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        try:
            user_permissions = self.get_user_permissions(user_id)
            return bool(user_permissions.intersection(set(permissions)))
            
        except Exception as e:
            self.logger.error(f"Error checking permissions: {e}")
            return False
    
    def has_all_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        try:
            user_permissions = self.get_user_permissions(user_id)
            return set(permissions).issubset(user_permissions)
            
        except Exception as e:
            self.logger.error(f"Error checking permissions: {e}")
            return False
    
    def check_resource_access(self, user_id: int, resource_type: str, resource_id: str, action: str) -> bool:
        """Check if user can perform action on specific resource"""
        try:
            # Get user info
            user = user_manager.get_user_by_id(user_id)
            if not user:
                return False
            
            # Admin has access to everything
            if user.get('role_name') == 'admin':
                return True
            
            # Check resource-specific permissions
            if resource_type == 'user':
                # Users can only modify their own profile (except admins)
                if action in ['update', 'read'] and str(user_id) == resource_id:
                    return True
                # Only admins can create/delete users
                if action in ['create', 'delete', 'activate', 'deactivate']:
                    return False
            
            elif resource_type == 'file':
                # Check file ownership or permissions
                if action == 'read':
                    return self.has_permission(user_id, Permission.FILE_READ)
                elif action == 'upload':
                    return self.has_permission(user_id, Permission.FILE_UPLOAD)
                elif action == 'delete':
                    return self.has_permission(user_id, Permission.FILE_DELETE)
            
            elif resource_type == 'reconciliation':
                if action == 'create':
                    return self.has_permission(user_id, Permission.RECONCILIATION_CREATE)
                elif action == 'read':
                    return self.has_permission(user_id, Permission.RECONCILIATION_READ)
                elif action == 'approve':
                    return self.has_permission(user_id, Permission.RECONCILIATION_APPROVE)
            
            # Default permission check
            permission = f"{resource_type}:{action}"
            return self.has_permission(user_id, permission)
            
        except Exception as e:
            self.logger.error(f"Error checking resource access: {e}")
            return False
    
    def get_user_role_info(self, user_id: int) -> Dict:
        """Get user's role information and permissions"""
        try:
            user = user_manager.get_user_by_id(user_id)
            if not user:
                return {}
            
            role_name = user.get('role_name', '')
            role_info = Role.get_all_roles().get(role_name, {})
            
            return {
                'role_name': role_name,
                'role_display_name': role_info.get('name', ''),
                'role_description': role_info.get('description', ''),
                'permissions': list(self.get_user_permissions(user_id))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user role info: {e}")
            return {}

# Decorators for route protection
def require_permission(permission: str):
    """Decorator to require a specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get current user from request
            current_user = getattr(request, 'current_user', None)
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'error_code': 'UNAUTHORIZED'
                }), 401
            
            user_id = current_user.get('user_id')
            if not user_id:
                return jsonify({
                    'success': False,
                    'message': 'Invalid user session',
                    'error_code': 'INVALID_SESSION'
                }), 401
            
            # Check permission
            auth_service = AuthorizationService()
            if not auth_service.has_permission(user_id, permission):
                # Log unauthorized access attempt
                security_logger.log_suspicious_activity(
                    'unauthorized_access',
                    f'User {user_id} attempted to access {request.endpoint} without permission {permission}',
                    user_id=user_id,
                    ip_address=request.remote_addr
                )
                
                return jsonify({
                    'success': False,
                    'message': 'Access denied',
                    'error_code': 'FORBIDDEN'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_permission(permissions: List[str]):
    """Decorator to require any of the specified permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(request, 'current_user', None)
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'error_code': 'UNAUTHORIZED'
                }), 401
            
            user_id = current_user.get('user_id')
            if not user_id:
                return jsonify({
                    'success': False,
                    'message': 'Invalid user session',
                    'error_code': 'INVALID_SESSION'
                }), 401
            
            # Check permissions
            auth_service = AuthorizationService()
            if not auth_service.has_any_permission(user_id, permissions):
                security_logger.log_suspicious_activity(
                    'unauthorized_access',
                    f'User {user_id} attempted to access {request.endpoint} without required permissions',
                    user_id=user_id,
                    ip_address=request.remote_addr
                )
                
                return jsonify({
                    'success': False,
                    'message': 'Access denied',
                    'error_code': 'FORBIDDEN'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_all_permissions(permissions: List[str]):
    """Decorator to require all of the specified permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(request, 'current_user', None)
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'error_code': 'UNAUTHORIZED'
                }), 401
            
            user_id = current_user.get('user_id')
            if not user_id:
                return jsonify({
                    'success': False,
                    'message': 'Invalid user session',
                    'error_code': 'INVALID_SESSION'
                }), 401
            
            # Check permissions
            auth_service = AuthorizationService()
            if not auth_service.has_all_permissions(user_id, permissions):
                security_logger.log_suspicious_activity(
                    'unauthorized_access',
                    f'User {user_id} attempted to access {request.endpoint} without all required permissions',
                    user_id=user_id,
                    ip_address=request.remote_addr
                )
                
                return jsonify({
                    'success': False,
                    'message': 'Access denied',
                    'error_code': 'FORBIDDEN'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role_name: str):
    """Decorator to require a specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(request, 'current_user', None)
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'error_code': 'UNAUTHORIZED'
                }), 401
            
            user_role = current_user.get('role_name')
            if user_role != role_name:
                security_logger.log_suspicious_activity(
                    'unauthorized_access',
                    f'User {current_user.get("user_id")} attempted to access {request.endpoint} without required role {role_name}',
                    user_id=current_user.get('user_id'),
                    ip_address=request.remote_addr
                )
                
                return jsonify({
                    'success': False,
                    'message': 'Access denied',
                    'error_code': 'FORBIDDEN'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin():
    """Decorator to require admin role"""
    return require_role('admin')

# Global authorization service instance
authorization_service = AuthorizationService()
