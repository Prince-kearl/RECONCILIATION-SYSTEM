"""
Flask App Configuration for Supabase Integration
This shows how to configure SQLAlchemy with both MySQL and PostgreSQL
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    UPLOAD_FOLDER = './uploads'
    OUTPUT_FOLDER = './outputs'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

class MySQLConfig(Config):
    """MySQL Configuration (Legacy)"""
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'reconx')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

class PostgreSQLConfig(Config):
    """PostgreSQL Configuration (Supabase)"""
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_SSLMODE = os.getenv('DB_SSLMODE', 'require')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'connect_args': {
            'sslmode': DB_SSLMODE,
        }
    }

def get_config():
    """Get configuration based on DB_TYPE environment variable"""
    db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    if db_type == 'postgresql':
        return PostgreSQLConfig()
    else:
        return MySQLConfig()

# Get active configuration
config = get_config()

print(f"✅ Using {config.__class__.__name__}")
print(f"   Host: {config.DB_HOST}")
print(f"   Port: {config.DB_PORT}")
print(f"   Database: {config.DB_NAME}")
