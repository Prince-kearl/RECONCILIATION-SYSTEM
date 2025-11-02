"""
ReconX API Response Utilities
Standardized API responses and error handling
"""

from typing import Any, Dict, Optional, Union
from flask import jsonify
from utils.logger import api_logger

class APIResponse:
    """Standardized API response class"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """Return success response"""
        response = {
            'success': True,
            'message': message,
            'data': data
        }
        
        # Log successful response
        api_logger.log_response(
            method=request.method if request else 'UNKNOWN',
            endpoint=request.endpoint if request else 'UNKNOWN',
            status_code=status_code,
            response_time=0.0  # Will be calculated by middleware
        )
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str, error_code: str = None, status_code: int = 400, 
              details: Any = None) -> tuple:
        """Return error response"""
        response = {
            'success': False,
            'message': message,
            'error_code': error_code
        }
        
        if details:
            response['details'] = details
        
        # Log error response
        if request:
            api_logger.log_error(
                method=request.method,
                endpoint=request.endpoint,
                error=Exception(message),
                user_id=getattr(request, 'current_user', {}).get('user_id') if hasattr(request, 'current_user') else None
            )
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors: list, message: str = "Validation failed") -> tuple:
        """Return validation error response"""
        return APIResponse.error(
            message=message,
            error_code='VALIDATION_ERROR',
            status_code=422,
            details={'validation_errors': errors}
        )
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> tuple:
        """Return not found response"""
        return APIResponse.error(
            message=message,
            error_code='NOT_FOUND',
            status_code=404
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> tuple:
        """Return unauthorized response"""
        return APIResponse.error(
            message=message,
            error_code='UNAUTHORIZED',
            status_code=401
        )
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> tuple:
        """Return forbidden response"""
        return APIResponse.error(
            message=message,
            error_code='FORBIDDEN',
            status_code=403
        )
    
    @staticmethod
    def server_error(message: str = "Internal server error", details: Any = None) -> tuple:
        """Return server error response"""
        return APIResponse.error(
            message=message,
            error_code='INTERNAL_ERROR',
            status_code=500,
            details=details
        )
    
    @staticmethod
    def rate_limited(message: str = "Too many requests", retry_after: int = None) -> tuple:
        """Return rate limited response"""
        response = {
            'success': False,
            'message': message,
            'error_code': 'RATE_LIMITED'
        }
        
        if retry_after:
            response['retry_after'] = retry_after
        
        return jsonify(response), 429

def handle_exception(error: Exception, context: str = None) -> tuple:
    """Handle exceptions and return appropriate API response"""
    error_type = type(error).__name__
    error_message = str(error)
    
    # Log the exception
    if context:
        api_logger.log_error(
            method=request.method if request else 'UNKNOWN',
            endpoint=context,
            error=error,
            user_id=getattr(request, 'current_user', {}).get('user_id') if hasattr(request, 'current_user') else None
        )
    
    # Handle specific exception types
    if isinstance(error, ValueError):
        return APIResponse.validation_error([error_message])
    
    elif isinstance(error, KeyError):
        return APIResponse.error(
            message=f"Missing required field: {error_message}",
            error_code='MISSING_FIELD',
            status_code=400
        )
    
    elif isinstance(error, TypeError):
        return APIResponse.error(
            message="Invalid data type",
            error_code='INVALID_TYPE',
            status_code=400
        )
    
    elif isinstance(error, FileNotFoundError):
        return APIResponse.not_found("File not found")
    
    elif isinstance(error, PermissionError):
        return APIResponse.forbidden("Permission denied")
    
    else:
        # Generic server error for unexpected exceptions
        return APIResponse.server_error(
            message="An unexpected error occurred",
            details={
                'error_type': error_type,
                'error_message': error_message
            }
        )

def validate_required_fields(data: dict, required_fields: list) -> tuple:
    """Validate that required fields are present"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None

def validate_field_types(data: dict, field_types: dict) -> tuple:
    """Validate field types"""
    type_errors = []
    
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                type_errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
    
    if type_errors:
        return False, type_errors
    
    return True, None

def sanitize_response_data(data: Any) -> Any:
    """Sanitize response data to prevent sensitive information leakage"""
    if isinstance(data, dict):
        # Remove sensitive fields
        sensitive_fields = ['password', 'password_hash', 'token', 'secret']
        sanitized = {}
        
        for key, value in data.items():
            if key.lower() not in [field.lower() for field in sensitive_fields]:
                if isinstance(value, (dict, list)):
                    sanitized[key] = sanitize_response_data(value)
                else:
                    sanitized[key] = value
        
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_response_data(item) for item in data]
    
    else:
        return data

def paginate_response(data: list, page: int = 1, per_page: int = 20, 
                     total_count: int = None) -> dict:
    """Create paginated response structure"""
    if total_count is None:
        total_count = len(data)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return {
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

# Import request for logging (avoid circular imports)
from flask import request
