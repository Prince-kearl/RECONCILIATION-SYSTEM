"""
ReconX Configuration Management
Centralized configuration loading and validation
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 8))  # hours
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 30))  # days
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'reconx')
    DB_CHARSET = 'utf8mb4'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', './outputs')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Security Configuration
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    LOGIN_MAX_ATTEMPTS = int(os.getenv('LOGIN_MAX_ATTEMPTS', 5))
    LOGIN_LOCKOUT_DURATION = int(os.getenv('LOGIN_LOCKOUT_DURATION', 15))  # minutes
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    
    # MFA Configuration
    MFA_ENABLED = os.getenv('MFA_ENABLED', 'True').lower() == 'true'
    MFA_ISSUER = os.getenv('MFA_ISSUER', 'ReconX')
    MFA_ALGORITHM = 'sha1'
    MFA_DIGITS = 6
    MFA_PERIOD = 30
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/reconx.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Reconciliation Configuration
    RECONCILIATION_BATCH_SIZE = int(os.getenv('RECONCILIATION_BATCH_SIZE', 1000))
    RECONCILIATION_TIMEOUT = int(os.getenv('RECONCILIATION_TIMEOUT', 300))  # seconds
    DEFAULT_TOLERANCE = float(os.getenv('DEFAULT_TOLERANCE', 0.00))
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check required environment variables
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            issues.append("SECRET_KEY should be changed in production")
        
        if cls.JWT_SECRET_KEY == 'dev-jwt-secret-change-in-production':
            issues.append("JWT_SECRET_KEY should be changed in production")
        
        # Check database configuration
        if not cls.DB_PASSWORD:
            issues.append("DB_PASSWORD is required")
        
        # Check file paths
        if not os.path.exists(cls.UPLOAD_FOLDER):
            issues.append(f"UPLOAD_FOLDER {cls.UPLOAD_FOLDER} does not exist")
        
        if not os.path.exists(cls.OUTPUT_FOLDER):
            issues.append(f"OUTPUT_FOLDER {cls.OUTPUT_FOLDER} does not exist")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': [issue for issue in issues if 'should be changed' in issue]
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # Override with production defaults
    RATE_LIMIT_ENABLED = True
    MFA_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DB_NAME = 'reconx_test'
    
    # Use in-memory database for testing
    DB_HOST = 'localhost'
    DB_USER = 'test_user'
    DB_PASSWORD = 'test_password'

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config(environment: str = None) -> Config:
    """Get configuration based on environment"""
    if not environment:
        environment = os.getenv('FLASK_ENV', 'development')
    
    config_class = config_map.get(environment, DevelopmentConfig)
    return config_class()

# Global config instance
config = get_config()

# Legacy database URI for backward compatibility
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
server = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{username}:{password}@{server}/{database}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
