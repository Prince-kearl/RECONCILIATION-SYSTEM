"""
Database configuration with support for MySQL and PostgreSQL (Supabase)
Seamlessly switch between databases via DB_TYPE environment variable
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration class - supports MySQL and PostgreSQL"""
    
    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'mysql').lower()  # 'mysql' or 'postgresql'
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306' if self.db_type == 'mysql' else '5432'))
        self.user = os.getenv('DB_USER', 'root' if self.db_type == 'mysql' else 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'reconx' if self.db_type == 'mysql' else 'postgres')
        self.charset = 'utf8mb4' if self.db_type == 'mysql' else None
        self.sslmode = os.getenv('DB_SSLMODE', 'disable' if self.db_type == 'mysql' else 'require')
    
    def get_connection_string(self):
        """Get SQLAlchemy connection string based on database type"""
        if self.db_type == 'postgresql':
            # PostgreSQL/Supabase connection string
            return f"postgresql+psycopg2://{self.user}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"
        else:
            # MySQL connection string (legacy)
            return f"mysql+pymysql://{self.user}:{quote_plus(self.password)}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
    
    def get_raw_connection(self):
        """Get raw database connection (for direct queries)"""
        if self.db_type == 'postgresql':
            import psycopg2
            try:
                connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    sslmode=self.sslmode
                )
                return connection
            except Exception as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                raise
        else:
            # MySQL
            import pymysql
            try:
                connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
                return connection
            except Exception as e:
                logger.error(f"MySQL connection failed: {e}")
                raise

class DatabaseManager:
    """Database manager for common operations"""
    
    def __init__(self):
        self.config = DatabaseConfig()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        connection = None
        try:
            connection = self.config.get_raw_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            cursor.close()
            return result if result else []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        connection = None
        try:
            connection = self.config.get_raw_connection()
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            affected_rows = cursor.rowcount
            
            if self.config.db_type == 'mysql':
                connection.commit()
            
            cursor.close()
            return affected_rows
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Update execution failed: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            connection = self.config.get_raw_connection()
            cursor = connection.cursor()
            
            if self.config.db_type == 'postgresql':
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1")
            
            cursor.close()
            connection.close()
            logger.info(f"✅ {self.config.db_type.upper()} Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

# Initialize managers
db_config = DatabaseConfig()
db_manager = DatabaseManager()

# Import the rest of the database managers (these remain unchanged)
# They will use the new connection strings
try:
    from .legacy_managers import user_manager, file_manager, reconciliation_manager, audit_manager
except ImportError:
    # Create placeholder managers for initial setup
    user_manager = db_manager
    file_manager = db_manager
    reconciliation_manager = db_manager
    audit_manager = db_manager
    logger.warning("Legacy managers not found - using DatabaseManager directly")
