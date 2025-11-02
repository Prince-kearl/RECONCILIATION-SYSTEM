"""
ReconX Logging System
Centralized logging with file rotation and structured formatting
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
from config import config

class ReconXLogger:
    """Centralized logging system for ReconX"""
    
    def __init__(self, name: str = 'reconx'):
        self.name = name
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """Setup logger with handlers and formatters"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if not os.path.exists(os.path.dirname(config.LOG_FILE)):
            os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_SIZE,
            backupCount=config.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)

class APILogger:
    """Specialized logger for API operations"""
    
    def __init__(self):
        self.logger = ReconXLogger('reconx.api')
    
    def log_request(self, method: str, endpoint: str, user_id: Optional[int] = None, 
                   ip_address: Optional[str] = None, **kwargs):
        """Log API request"""
        self.logger.info(
            f"API Request: {method} {endpoint}",
            user_id=user_id,
            ip_address=ip_address,
            **kwargs
        )
    
    def log_response(self, method: str, endpoint: str, status_code: int, 
                    response_time: float, user_id: Optional[int] = None, **kwargs):
        """Log API response"""
        self.logger.info(
            f"API Response: {method} {endpoint} - {status_code} ({response_time:.3f}s)",
            user_id=user_id,
            status_code=status_code,
            response_time=response_time,
            **kwargs
        )
    
    def log_error(self, method: str, endpoint: str, error: Exception, 
                  user_id: Optional[int] = None, **kwargs):
        """Log API error"""
        self.logger.error(
            f"API Error: {method} {endpoint} - {str(error)}",
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = ReconXLogger('reconx.security')
    
    def log_login_attempt(self, username: str, success: bool, ip_address: str, **kwargs):
        """Log login attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"Login {status}: {username}",
            username=username,
            success=success,
            ip_address=ip_address,
            **kwargs
        )
    
    def log_failed_login(self, username: str, ip_address: str, reason: str, **kwargs):
        """Log failed login with reason"""
        self.logger.warning(
            f"Failed login: {username} - {reason}",
            username=username,
            ip_address=ip_address,
            reason=reason,
            **kwargs
        )
    
    def log_suspicious_activity(self, activity_type: str, details: str, 
                               user_id: Optional[int] = None, ip_address: Optional[str] = None, **kwargs):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity: {activity_type} - {details}",
            activity_type=activity_type,
            details=details,
            user_id=user_id,
            ip_address=ip_address,
            **kwargs
        )

class ReconciliationLogger:
    """Specialized logger for reconciliation operations"""
    
    def __init__(self):
        self.logger = ReconXLogger('reconx.reconciliation')
    
    def log_reconciliation_start(self, run_id: str, user_id: int, 
                               bank_count: int, collection_count: int, **kwargs):
        """Log reconciliation start"""
        self.logger.info(
            f"Reconciliation started: {run_id}",
            run_id=run_id,
            user_id=user_id,
            bank_count=bank_count,
            collection_count=collection_count,
            **kwargs
        )
    
    def log_reconciliation_complete(self, run_id: str, user_id: int, 
                                  matched_count: int, unmatched_count: int, 
                                  processing_time: float, **kwargs):
        """Log reconciliation completion"""
        self.logger.info(
            f"Reconciliation completed: {run_id} - {matched_count} matched, {unmatched_count} unmatched",
            run_id=run_id,
            user_id=user_id,
            matched_count=matched_count,
            unmatched_count=unmatched_count,
            processing_time=processing_time,
            **kwargs
        )
    
    def log_reconciliation_error(self, run_id: str, user_id: int, error: Exception, **kwargs):
        """Log reconciliation error"""
        self.logger.error(
            f"Reconciliation error: {run_id} - {str(error)}",
            run_id=run_id,
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )

# Global logger instances
logger = ReconXLogger()
api_logger = APILogger()
security_logger = SecurityLogger()
reconciliation_logger = ReconciliationLogger()

def get_logger(name: str = 'reconx') -> ReconXLogger:
    """Get a logger instance by name"""
    return ReconXLogger(name)
