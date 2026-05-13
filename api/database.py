"""
Database configuration and utilities for ReconX
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

try:
    import pymysql
except Exception:  # pragma: no cover - optional when running postgres-only
    pymysql = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover - optional when running mysql-only
    psycopg2 = None
    RealDictCursor = None

logger = logging.getLogger(__name__)

# Support both conventional .env and this repo's config.env naming.
load_dotenv('.env')
load_dotenv('config.env')
load_dotenv('.env.supabase')

class DatabaseConfig:
    """Database configuration class"""
    
    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'mysql').lower()
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306 if self.db_type == 'mysql' else 5432))
        self.user = os.getenv('DB_USER', 'root' if self.db_type == 'mysql' else 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'reconx' if self.db_type == 'mysql' else 'postgres')
        self.charset = 'utf8mb4'
        self.sslmode = os.getenv('DB_SSLMODE', 'require' if self.db_type == 'postgresql' else 'disable')
    
    def get_connection(self):
        """Get database connection"""
        try:
            if self.db_type == 'postgresql':
                if psycopg2 is None:
                    raise RuntimeError("psycopg2 is required for DB_TYPE=postgresql")
                connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.database,
                    sslmode=self.sslmode,
                    cursor_factory=RealDictCursor,
                )
            else:
                if pymysql is None:
                    raise RuntimeError("pymysql is required for DB_TYPE=mysql")
                connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset=self.charset,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
            return connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

class DatabaseManager:
    """Database manager for common operations"""
    
    def __init__(self):
        self.config = DatabaseConfig()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        connection = None
        try:
            connection = self.config.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return list(cursor.fetchall())
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        connection = None
        try:
            connection = self.config.get_connection()
            with connection.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                connection.commit()
                return affected_rows
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT query and return the last insert ID"""
        connection = None
        try:
            connection = self.config.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                if self.config.db_type == 'postgresql':
                    last_id = None
                    try:
                        returned = cursor.fetchone()
                        if isinstance(returned, dict):
                            first_value = next(iter(returned.values()), None)
                            if first_value is not None:
                                last_id = int(first_value)
                    except Exception:
                        last_id = None

                    if last_id is None:
                        cursor.execute("SELECT LASTVAL() AS id")
                        row = cursor.fetchone() or {}
                        last_id = int(row.get('id', 0) or 0)
                else:
                    last_id = cursor.lastrowid
                connection.commit()
                return last_id
        except Exception as e:
            logger.error(f"Insert execution failed: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()

# User management functions
class UserManager:
    """User management operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        query = """
            SELECT u.*, r.role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.username = %s
        """
        results = self.db.execute_query(query, (username,))
        return results[0] if results else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
            SELECT u.*, r.role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.user_id = %s
        """
        results = self.db.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def create_user(self, username: str, password_hash: str, full_name: str, 
                   email: str, role_id: int) -> int:
        """Create a new user"""
        query = """
            INSERT INTO users (username, password_hash, full_name, email, role_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (username, password_hash, full_name, email, role_id))
    
    def get_all_users(self) -> List[Dict]:
        """Get all users with their roles"""
        query = """
            SELECT u.*, r.role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            ORDER BY u.created_at DESC
        """
        return self.db.execute_query(query)
    
    def update_user_status(self, user_id: int, status: str) -> bool:
        """Update user status"""
        query = "UPDATE users SET status = %s WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (status, user_id))
        return affected_rows > 0
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        query = "UPDATE users SET last_login = %s WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (datetime.now(), user_id))
        return affected_rows > 0
    
    def update_failed_login_attempts(self, user_id: int, attempts: int) -> bool:
        """Update failed login attempts count"""
        query = "UPDATE users SET failed_login_attempts = %s WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (attempts, user_id))
        return affected_rows > 0
    
    def reset_failed_login_attempts(self, user_id: int) -> bool:
        """Reset failed login attempts to 0"""
        query = "UPDATE users SET failed_login_attempts = 0 WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (user_id,))
        return affected_rows > 0
    
    def lock_account(self, user_id: int, lockout_until: datetime) -> bool:
        """Lock user account until specified time"""
        query = "UPDATE users SET status = 'locked', account_locked_until = %s WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (lockout_until, user_id))
        return affected_rows > 0
    
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password"""
        query = "UPDATE users SET password_hash = %s, password_changed_at = %s WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (password_hash, datetime.now(), user_id))
        return affected_rows > 0
    
    def enable_mfa(self, user_id: int) -> bool:
        """Enable MFA for user"""
        query = "UPDATE users SET mfa_enabled = TRUE WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (user_id,))
        return affected_rows > 0
    
    def disable_mfa(self, user_id: int) -> bool:
        """Disable MFA for user"""
        query = "UPDATE users SET mfa_enabled = FALSE WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (user_id,))
        return affected_rows > 0
    
    def create_mfa_secret(self, user_id: int, secret_key: str, backup_codes: list) -> int:
        """Create MFA secret for user"""
        import json
        query = """
            INSERT INTO mfa_secrets (user_id, secret_key, backup_codes)
            VALUES (%s, %s, %s)
        """
        return self.db.execute_insert(query, (user_id, secret_key, json.dumps(backup_codes)))
    
    def get_mfa_secret(self, user_id: int) -> Optional[Dict]:
        """Get user's MFA secret"""
        query = """
            SELECT secret_key, backup_codes, is_active
            FROM mfa_secrets
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """
        results = self.db.execute_query(query, (user_id,))
        if results:
            import json
            result = results[0]
            result['backup_codes'] = json.loads(result['backup_codes']) if result['backup_codes'] else []
            return result
        return None
    
    def use_backup_code(self, user_id: int, code: str) -> bool:
        """Use a backup code (remove it from the list)"""
        mfa_secret = self.get_mfa_secret(user_id)
        if not mfa_secret or code not in mfa_secret['backup_codes']:
            return False
        
        # Remove the used backup code
        backup_codes = mfa_secret['backup_codes']
        backup_codes.remove(code)
        
        import json
        query = "UPDATE mfa_secrets SET backup_codes = %s WHERE user_id = %s AND is_active = TRUE"
        affected_rows = self.db.execute_update(query, (json.dumps(backup_codes), user_id))
        return affected_rows > 0
    
    def create_user_session(self, session_id: str, user_id: int, token_hash: str, 
                           expires_at: datetime, ip_address: str, user_agent: str) -> bool:
        """Create user session"""
        query = """
            INSERT INTO user_sessions (session_id, user_id, token_hash, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            self.db.execute_insert(query, (session_id, user_id, token_hash, expires_at, ip_address, user_agent))
            return True
        except Exception:
            return False
    
    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """Get user's active sessions"""
        query = """
            SELECT session_id, ip_address, user_agent, created_at, last_activity, expires_at
            FROM user_sessions
            WHERE user_id = %s AND is_active = TRUE AND expires_at > %s
            ORDER BY last_activity DESC
        """
        return self.db.execute_query(query, (user_id, datetime.now()))
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a specific session"""
        query = "UPDATE user_sessions SET is_active = FALSE WHERE session_id = %s"
        affected_rows = self.db.execute_update(query, (session_id,))
        return affected_rows > 0
    
    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user"""
        query = "UPDATE user_sessions SET is_active = FALSE WHERE user_id = %s"
        affected_rows = self.db.execute_update(query, (user_id,))
        return affected_rows > 0

# File upload and processing functions
class FileManager:
    """File upload and processing operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_file_upload(self, file_id: str, user_id: int, filename: str) -> bool:
        """Create a new file upload record using actual schema"""
        query = """
            INSERT INTO file_uploads (file_id, user_id, filename)
            VALUES (%s, %s, %s)
        """
        try:
            self.db.execute_insert(query, (file_id, user_id, filename))
            return True
        except Exception as e:
            logger.error(f"Error creating file upload: {e}")
            return False
    
    def update_file_upload_status(self, upload_id: int, status: str, **kwargs) -> bool:
        """Update file upload status and other fields"""
        set_clauses = []
        params = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        if set_clauses:
            query = f"UPDATE file_uploads SET status = %s, {', '.join(set_clauses)} WHERE upload_id = %s"
            params = [status] + params + [upload_id]
        else:
            query = "UPDATE file_uploads SET status = %s WHERE upload_id = %s"
            params = [status, upload_id]
        
        affected_rows = self.db.execute_update(query, tuple(params))
        return affected_rows > 0
    
    def get_file_upload(self, upload_id: int) -> Optional[Dict]:
        """Get file upload by ID"""
        query = """
            SELECT fu.*, u.username as uploaded_by_name
            FROM file_uploads fu
            JOIN users u ON fu.uploaded_by = u.user_id
            WHERE fu.upload_id = %s
        """
        results = self.db.execute_query(query, (upload_id,))
        return results[0] if results else None
    
    def get_file_uploads(self, file_type: str = None, status: str = None, limit: int = 100) -> List[Dict]:
        """Get file uploads with optional filtering"""
        where_clauses = []
        params = []
        
        if file_type:
            where_clauses.append("fu.file_type = %s")
            params.append(file_type)
        
        if status:
            where_clauses.append("fu.status = %s")
            params.append(status)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        params.append(limit)
        
        query = f"""
            SELECT fu.*, u.username as uploaded_by_name
            FROM file_uploads fu
            JOIN users u ON fu.uploaded_by = u.user_id
            {where_clause}
            ORDER BY fu.uploaded_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, tuple(params))
    
    def get_user_file_uploads(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get file uploads for a specific user"""
        query = """
            SELECT fu.*, u.username as uploaded_by_name
            FROM file_uploads fu
            JOIN users u ON fu.uploaded_by = u.user_id
            WHERE fu.uploaded_by = %s
            ORDER BY fu.uploaded_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (user_id, limit))
    
    def save_bank_statement(self, file_id: str, transaction_date: str, amount: float, 
                           description: str, account_number: str = None) -> int:
        """Save bank statement record using actual schema"""
        query = """
            INSERT INTO bank_statements 
            (bank_ref, transaction_date, amount, description, account_number, uploaded_by, file_name, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (
            file_id, transaction_date, amount, description, account_number, 
            1, f"bank_{file_id}.xlsx", f"uploads/bank_{file_id}.xlsx"  # Default values for required fields
        ))
    
    def save_internal_record(self, file_id: str, transaction_date: str, amount: float,
                            reference: str, description: str) -> int:
        """Save internal record using actual schema"""
        query = """
            INSERT INTO internal_records 
            (reference, transaction_date, amount, narration, uploaded_by, file_name, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (
            reference, transaction_date, amount, description, 
            1, f"internal_{file_id}.xlsx", f"uploads/internal_{file_id}.xlsx"  # Default values for required fields
        ))
    
    def get_bank_statements(self, limit: int = 100) -> List[Dict]:
        """Get recent bank statements"""
        query = """
            SELECT bs.*, u.username as uploaded_by_name
            FROM bank_statements bs
            JOIN users u ON bs.uploaded_by = u.user_id
            ORDER BY bs.uploaded_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_internal_records(self, limit: int = 100) -> List[Dict]:
        """Get recent internal records"""
        query = """
            SELECT ir.*, u.username as uploaded_by_name
            FROM internal_records ir
            JOIN users u ON ir.uploaded_by = u.user_id
            ORDER BY ir.uploaded_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_file_uploads_summary(self, limit: int = 50) -> List[Dict]:
        """Get file uploads summary using the view"""
        query = """
            SELECT 
                file_id as upload_id,
                filename,
                uploaded_at,
                uploaded_by,
                bank_records,
                internal_records,
                CASE 
                    WHEN bank_records > 0 THEN 'bank_statement'
                    WHEN internal_records > 0 THEN 'internal_record'
                    ELSE 'unknown'
                END as file_type,
                CASE 
                    WHEN bank_records > 0 OR internal_records > 0 THEN 'processed'
                    ELSE 'uploaded'
                END as status,
                (bank_records + internal_records) as records_count
            FROM v_file_upload_summary
            ORDER BY uploaded_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_latest_bank_file(self) -> Optional[Dict]:
        """Get latest bank statement file"""
        query = """
            SELECT 
                f.file_id as upload_id,
                f.filename,
                f.uploaded_at,
                u.username as uploaded_by_name,
                COUNT(b.statement_id) as records_count,
                'bank_statement' as file_type,
                'processed' as status
            FROM file_uploads f
            JOIN users u ON f.user_id = u.user_id
            LEFT JOIN bank_statements b ON f.file_id = b.file_id
            WHERE EXISTS (SELECT 1 FROM bank_statements WHERE file_id = f.file_id)
            GROUP BY f.file_id, f.filename, f.uploaded_at, u.username
            ORDER BY f.uploaded_at DESC
            LIMIT 1
        """
        results = self.db.execute_query(query)
        return results[0] if results else None
    
    def get_latest_internal_file(self) -> Optional[Dict]:
        """Get latest internal record file"""
        query = """
            SELECT 
                f.file_id as upload_id,
                f.filename,
                f.uploaded_at,
                u.username as uploaded_by_name,
                COUNT(i.record_id) as records_count,
                'internal_record' as file_type,
                'processed' as status
            FROM file_uploads f
            JOIN users u ON f.user_id = u.user_id
            LEFT JOIN internal_records i ON f.file_id = i.file_id
            WHERE EXISTS (SELECT 1 FROM internal_records WHERE file_id = f.file_id)
            GROUP BY f.file_id, f.filename, f.uploaded_at, u.username
            ORDER BY f.uploaded_at DESC
            LIMIT 1
        """
        results = self.db.execute_query(query)
        return results[0] if results else None

# Reconciliation functions
class ReconciliationManager:
    """Reconciliation operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def save_reconciliation_result(self, bank_statement_id: int, internal_record_id: int,
                                 status: str, difference: float, tolerance: float,
                                 matched_by: int, reconciliation_run_id: str) -> int:
        """Save reconciliation result"""
        query = """
            INSERT INTO reconciliation_results 
            (bank_statement_id, internal_record_id, status, difference, tolerance, matched_by, reconciliation_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (
            bank_statement_id, internal_record_id, status, difference, tolerance,
            matched_by, reconciliation_run_id
        ))
    
    def get_reconciliation_results(self, run_id: str = None, limit: int = 100) -> List[Dict]:
        """Get reconciliation results"""
        if run_id:
            query = """
                SELECT rr.*, bs.bank_ref, bs.description as bank_description, bs.amount as bank_amount,
                       ir.reference, ir.narration, ir.amount as internal_amount,
                       u.username as matched_by_name
                FROM reconciliation_results rr
                LEFT JOIN bank_statements bs ON rr.bank_statement_id = bs.statement_id
                LEFT JOIN internal_records ir ON rr.internal_record_id = ir.record_id
                LEFT JOIN users u ON rr.matched_by = u.user_id
                WHERE rr.reconciliation_run_id = %s
                ORDER BY rr.matched_at DESC
            """
            return self.db.execute_query(query, (run_id,))
        else:
            query = """
                SELECT rr.*, bs.bank_ref, bs.description as bank_description, bs.amount as bank_amount,
                       ir.reference, ir.narration, ir.amount as internal_amount,
                       u.username as matched_by_name
                FROM reconciliation_results rr
                LEFT JOIN bank_statements bs ON rr.bank_statement_id = bs.statement_id
                LEFT JOIN internal_records ir ON rr.internal_record_id = ir.record_id
                LEFT JOIN users u ON rr.matched_by = u.user_id
                ORDER BY rr.matched_at DESC
                LIMIT %s
            """
            return self.db.execute_query(query, (limit,))

# Audit logging functions
class AuditManager:
    """Audit logging operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def log_action(self, user_id: int, action: str, details: str = None, ip_address: str = None) -> int:
        """Log an audit action"""
        query = """
            INSERT INTO audit_logs (user_id, action, details, ip_address)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (user_id, action, details, ip_address))
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        query = """
            SELECT al.*, u.username, u.username as full_name
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            ORDER BY al.created_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))
    
    def get_user_audit_logs(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get audit logs for a specific user"""
        query = """
            SELECT al.*, u.username, u.username as full_name
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            WHERE al.user_id = %s
            ORDER BY al.created_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (user_id, limit))

# Reconciliation Runs functions
class ReconciliationRunsManager:
    """Reconciliation runs operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_run(self, run_id: str, user_id: int, tolerance: float, config: dict) -> int:
        """Create a new reconciliation run"""
        import json
        query = """
            INSERT INTO reconciliation_runs (run_id, user_id, tolerance, configuration, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """
        return self.db.execute_insert(query, (run_id, user_id, tolerance, json.dumps(config)))
    
    def update_run_status(self, run_id: str, status: str, **kwargs) -> bool:
        """Update reconciliation run status and other fields"""
        set_clauses = []
        params = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        query = f"UPDATE reconciliation_runs SET status = %s, {', '.join(set_clauses)} WHERE run_id = %s"
        params = [status] + params + [run_id]
        affected_rows = self.db.execute_update(query, tuple(params))
        return affected_rows > 0
    
    def get_run(self, run_id: str) -> Optional[Dict]:
        """Get reconciliation run by ID"""
        query = """
            SELECT rr.*, u.username, u.username as full_name
            FROM reconciliation_runs rr
            JOIN users u ON rr.user_id = u.user_id
            WHERE rr.run_id = %s
        """
        results = self.db.execute_query(query, (run_id,))
        return results[0] if results else None
    
    def get_user_runs(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get reconciliation runs for a user"""
        query = """
            SELECT rr.*, u.username, u.username as full_name
            FROM reconciliation_runs rr
            JOIN users u ON rr.user_id = u.user_id
            WHERE rr.user_id = %s
            ORDER BY rr.started_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (user_id, limit))
    
    def get_all_runs(self, limit: int = 100) -> List[Dict]:
        """Get all reconciliation runs"""
        query = """
            SELECT rr.*, u.username, u.username as full_name
            FROM reconciliation_runs rr
            JOIN users u ON rr.user_id = u.user_id
            ORDER BY rr.started_at DESC
            LIMIT %s
        """
        return self.db.execute_query(query, (limit,))

# Initialize managers
user_manager = UserManager()
file_manager = FileManager()
reconciliation_manager = ReconciliationManager()
reconciliation_runs_manager = ReconciliationRunsManager()
audit_manager = AuditManager()
