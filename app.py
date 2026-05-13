"""
ReconX MVP Backend
Core workflows: Authentication, File Upload, Reconciliation, Audit
"""

from flask import Flask, request, jsonify, send_file, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import os
import uuid
import logging
import json
from datetime import datetime, timedelta
import jwt
import pandas as pd
from functools import wraps
import threading
import queue
from typing import Dict
import time
from dotenv import load_dotenv

# Setup logging early so import-time fallbacks can log safely
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from either .env or config.env.
load_dotenv('.env')
load_dotenv('config.env')

# Import the ReconciliationEngine
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from reconciliation_system_production import ReconciliationEngine
except ImportError:
    logger.warning("Could not import ReconciliationEngine from reconciliation_system_production.py")
    ReconciliationEngine = None

# Import database managers
try:
    from .database import user_manager, file_manager, reconciliation_manager, audit_manager
except ImportError:
    from database import user_manager, file_manager, reconciliation_manager, audit_manager

# Import controllers
try:
    from .controllers import auth_controller, files_controller, reconciliation_controller, users_controller
except ImportError:
    from api.controllers import auth_controller, files_controller, reconciliation_controller, users_controller

app = Flask(__name__)
# Legacy static redirect for old upload page
@app.route('/upload.html')
def legacy_upload_redirect():
    return redirect('/upload_enhanced.html', code=302)

# Explicit CORS to satisfy browser preflight from file:// or 127.0.0.1:5501
CORS(
    app,
    resources={r"/api/*": {"origins": ["*", "http://127.0.0.1:5501", "http://localhost:5501"]}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    supports_credentials=False,
)

# Configuration
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
    UPLOAD_FOLDER='./uploads',
    OUTPUT_FOLDER='./outputs',
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB
    ALLOWED_EXTENSIONS={'csv', 'xlsx', 'xls'},
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8)
)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Background task queue for reconciliation processing
task_queue = queue.Queue()
processing_tasks = {}

class ReconciliationTask:
    def __init__(self, task_id: str, user_id: str, files: Dict, config: Dict):
        self.task_id = task_id
        self.user_id = user_id
        self.files = files
        self.config = config
        self.status = 'pending'
        self.progress = 0
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None

# Helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def validate_file_content(file_path, expected_columns=None):
    """Validate file content and structure"""
    try:
        ext = file_path.split('.')[-1].lower()
        if ext == 'csv':
            df = pd.read_csv(file_path, nrows=1)  # Read only first row to check structure
        else:
            df = pd.read_excel(file_path, nrows=1)
        
        if expected_columns:
            missing_cols = [col for col in expected_columns if col not in df.columns]
            if missing_cols:
                return False, f"Missing required columns: {missing_cols}"
        
        return True, "File structure is valid"
    except Exception as e:
        return False, f"File validation failed: {str(e)}"

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks"""
    import re
    # Remove any path components and dangerous characters
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return filename

def validate_amount(amount):
    """Validate and convert amount to float"""
    try:
        if amount is None or amount == '':
            return 0.00
        return float(amount)
    except (ValueError, TypeError):
        return 0.00

def validate_date(date_value):
    """Validate and convert date to ISO format"""
    try:
        if pd.isna(date_value) or date_value is None or date_value == '':
            return datetime.utcnow().date().isoformat()
        
        if isinstance(date_value, str):
            return pd.to_datetime(date_value).date().isoformat()
        else:
            return pd.to_datetime(date_value).date().isoformat()
    except:
        return datetime.utcnow().date().isoformat()

# Simple rate limiting
rate_limit_storage = {}

def rate_limit(max_requests=10, window_seconds=60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage.get(client_ip, [])
                if current_time - req_time < window_seconds
            ]
            
            # Check if limit exceeded
            if len(rate_limit_storage.get(client_ip, [])) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {max_requests} per {window_seconds} seconds',
                    'retry_after': window_seconds
                }), 429
            
            # Add current request
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            rate_limit_storage[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def log_audit(user_id, action, details=None):
    """Log audit events"""
    try:
        audit_manager.log_action(
            user_id=user_id,
            action=action,
            details=json.dumps(details) if details else None,
            ip_address=request.remote_addr
        )
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")

# Authentication decorator
try:
    from .middleware.auth import require_auth
except ImportError:
    from api.middleware.auth import require_auth

def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = request.current_user['role_name']
            if user_role != role and user_role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Register controller blueprints
try:
    try:
        from .controllers.auth_controller import auth_bp
    except ImportError:
        from api.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
except Exception as e:
    logger.warning(f'Auth controller not registered: {e}')

try:
    try:
        from .controllers.files_controller import files_bp
    except ImportError:
        from api.controllers.files_controller import files_bp
    app.register_blueprint(files_bp, url_prefix='/api/files')
except Exception as e:
    logger.warning(f'Files controller not registered: {e}')

try:
    try:
        from .controllers.reconciliation_controller import recon_bp
    except ImportError:
        from api.controllers.reconciliation_controller import recon_bp
    app.register_blueprint(recon_bp, url_prefix='/api/reconciliation')
except Exception as e:
    logger.warning(f'Reconciliation controller not registered: {e}')

try:
    try:
        from .controllers.users_controller import users_bp
    except ImportError:
        from api.controllers.users_controller import users_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')
except Exception as e:
    logger.warning(f'Users controller not registered: {e}')

# Core API endpoints
@app.route('/api/auth/me', methods=['GET'])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def get_current_user():
    """Get current user info"""
    return jsonify({
        'id': request.current_user['user_id'],
        'username': request.current_user['username'],
        'email': request.current_user['email'],
        'role': request.current_user['role_name'],
        'full_name': request.current_user['full_name']
    })

@app.route('/api/reconciliation/results', methods=['GET'])
@require_auth
def get_reconciliation_results():
    """Get reconciliation results"""
    try:
        run_id = request.args.get('run_id')
        results = reconciliation_manager.get_reconciliation_results(run_id=run_id)
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error fetching reconciliation results: {e}")
        return jsonify({'error': 'Failed to fetch results'}), 500

# Note: File upload endpoints are now handled by controllers
# See files_controller.py for /api/files/upload/bank-statement and /api/files/upload/internal-record

# Reconciliation endpoints
@app.route('/api/reconciliation/start', methods=['POST'])
@require_auth
@rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
def start_reconciliation():
    """Start reconciliation process"""
    try:
        # Debug: Check if current_user exists
        if not hasattr(request, 'current_user'):
            logger.error("request.current_user not found - auth decorator failed")
            return jsonify({'error': 'Authentication failed'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        bank_file_id = data.get('bank_file_id')
        internal_file_id = data.get('internal_file_id')
        config = data.get('config', {})
        
        if not bank_file_id or not internal_file_id:
            return jsonify({'error': 'Both bank and internal file IDs are required'}), 400
        
        # Find uploaded files
        bank_file_path = None
        internal_file_path = None
        
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if bank_file_id in filename and filename.startswith('bank_statement_'):
                bank_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            elif internal_file_id in filename and filename.startswith('internal_record_'):
                internal_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not bank_file_path or not internal_file_path:
            return jsonify({'error': 'One or more uploaded files not found'}), 404
        
        # Create reconciliation task
        task_id = str(uuid.uuid4())
        task = ReconciliationTask(
            task_id=task_id,
            user_id=str(request.current_user['user_id']),
            files={
                'bank_statement': bank_file_path,
                'internal_record': internal_file_path
            },
            config=config
        )
        
        # Add to processing queue
        task_queue.put(task)
        
        # Persist reconciliation run start
        try:
            try:
                from .database import DatabaseManager
            except ImportError:
                from database import DatabaseManager
            db = DatabaseManager()
            db.execute_insert(
                "INSERT INTO reconciliation_runs (run_id, user_id, status, tolerance, configuration, started_at) VALUES (%s,%s,%s,%s,%s,NOW())",
                (task_id, int(request.current_user['user_id']), 'processing', float(config.get('tolerance', 0.00)), json.dumps(config))
            )
        except Exception as e:
            logger.error(f"Failed to persist reconciliation run start: {e}")

        # Log reconciliation start
        log_audit(request.current_user['user_id'], 'reconciliation_started', {
            'task_id': task_id,
            'bank_file': os.path.basename(bank_file_path),
            'internal_file': os.path.basename(internal_file_path),
            'config': config
        })
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Reconciliation started successfully',
            'status_url': f"/api/reconciliation/status/{task_id}"
        })
        
    except Exception as e:
        logger.error(f"Start reconciliation error: {str(e)}")
        return jsonify({'error': 'Failed to start reconciliation'}), 500

@app.route('/api/reconciliation/status/<task_id>', methods=['GET'])
@require_auth
def get_reconciliation_status(task_id):
    """Get reconciliation task status"""
    try:
        task = processing_tasks.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        response = {
            'task_id': task_id,
            'status': task.status,
            'progress': task.progress,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None
        }
        
        if task.status == 'completed':
            response['result'] = task.result
        elif task.status == 'failed':
            response['error'] = task.error
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Get status error: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

# Dashboard and reporting endpoints
@app.route('/api/dashboard/summary', methods=['GET'])
@require_auth
def get_dashboard_summary():
    """Get dashboard summary data"""
    try:
        # Get file upload summary
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        db = DatabaseManager()
        
        # Bank statements count
        bank_count = db.execute_query("SELECT COUNT(*) as count FROM bank_statements")[0]['count']
        internal_count = db.execute_query("SELECT COUNT(*) as count FROM internal_records")[0]['count']
        
        # Recent reconciliation runs
        recent_runs = db.execute_query("""
            SELECT * FROM v_reconciliation_summary 
            ORDER BY started_at DESC LIMIT 5
        """)
        
        return jsonify({
            'file_counts': {
                'bank_statements': bank_count,
                'internal_records': internal_count
            },
            'recent_reconciliations': recent_runs
        })
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard summary'}), 500

@app.route('/api/reports/reconciliation-summary', methods=['GET'])
@require_auth
def get_reconciliation_summary():
    """Get reconciliation summary report"""
    try:
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        db = DatabaseManager()
        
        summary = db.execute_query("SELECT * FROM v_reconciliation_summary ORDER BY started_at DESC")
        
        return jsonify({
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Reconciliation summary error: {str(e)}")
        return jsonify({'error': 'Failed to get reconciliation summary'}), 500

# Frontend integration compatibility endpoints (database-backed)
def _db_manager():
    try:
        from .database import DatabaseManager
    except ImportError:
        from database import DatabaseManager
    return DatabaseManager()


def _query_rows(query, params=None):
    try:
        db = _db_manager()
        return db.execute_query(query, params or ())
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return []


def _execute_update(query, params=None):
    db = _db_manager()
    return db.execute_update(query, params or ())


def _execute_insert(query, params=None):
    db = _db_manager()
    return db.execute_insert(query, params or ())


def _resolve_user_id():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1].strip()
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            user_id = payload.get('user_id') or payload.get('sub')
            if user_id:
                return int(user_id)
        except Exception:
            pass

    user = _query_rows("SELECT user_id FROM users WHERE status='active' ORDER BY user_id ASC LIMIT 1")
    return int(user[0]['user_id']) if user else None


def _time_ago(dt_value):
    try:
        dt = pd.to_datetime(dt_value).to_pydatetime()
        now = datetime.utcnow()
        delta = max(0, int((now - dt).total_seconds()))
        if delta < 60:
            return f"{delta}s ago"
        if delta < 3600:
            return f"{delta // 60} min ago"
        if delta < 86400:
            return f"{delta // 3600}h ago"
        return f"{delta // 86400}d ago"
    except Exception:
        return "-"


@app.route('/api/reports/filters', methods=['GET'])
def reports_filters():
    types = [r['file_type'] for r in _query_rows("SELECT DISTINCT file_type FROM file_uploads WHERE file_type IS NOT NULL ORDER BY file_type")]
    categories = [r['status'] for r in _query_rows("SELECT DISTINCT status FROM reconciliation_results WHERE status IS NOT NULL ORDER BY status")]
    sources = [r['status'] for r in _query_rows("SELECT DISTINCT status FROM file_uploads WHERE status IS NOT NULL ORDER BY status")]
    return jsonify({'types': types, 'categories': categories, 'sources': sources})


@app.route('/api/reports', methods=['GET'])
def reports_list():
    page = max(1, int(request.args.get('page', 1)))
    size = max(1, min(100, int(request.args.get('size', 10))))
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    prepared_by = request.args.get('preparedBy')

    where = []
    params = []
    if from_date:
        where.append("DATE(rr.started_at) >= %s")
        params.append(from_date)
    if to_date:
        where.append("DATE(rr.started_at) <= %s")
        params.append(to_date)
    if prepared_by:
        where.append("(u.email = %s OR u.username = %s)")
        params.extend([prepared_by, prepared_by])

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    total_row = _query_rows(
        f"""
        SELECT COUNT(*) AS total
        FROM reconciliation_runs rr
        LEFT JOIN users u ON rr.user_id = u.user_id
        {where_sql}
        """,
        tuple(params),
    )
    total = int(total_row[0]['total']) if total_row else 0

    offset = (page - 1) * size
    rows = _query_rows(
        f"""
        SELECT rr.run_id, rr.started_at, rr.status, rr.output_file_path,
               u.email, u.username
        FROM reconciliation_runs rr
        LEFT JOIN users u ON rr.user_id = u.user_id
        {where_sql}
        ORDER BY rr.started_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params + [size, offset]),
    )

    items = []
    for r in rows:
        file_name = os.path.basename(r.get('output_file_path') or '') or f"reconciliation_{r['run_id']}.xlsx"
        items.append({
            'id': r['run_id'],
            'fileName': file_name,
            'date': r['started_at'],
            'status': str(r.get('status') or '').replace('_', ' ').title(),
            'preparedBy': r.get('email') or r.get('username') or ''
        })

    return jsonify({'items': items, 'total': total})


@app.route('/api/reports/<report_id>/export', methods=['POST'])
def reports_export(report_id):
    fmt = (request.args.get('format') or 'csv').lower()
    run = _query_rows(
        "SELECT run_id, output_file_path, started_at, status FROM reconciliation_runs WHERE run_id = %s LIMIT 1",
        (report_id,),
    )
    if not run:
        return jsonify({'error': 'Report not found'}), 404

    run = run[0]
    if fmt == 'xlsx' and run.get('output_file_path') and os.path.exists(run['output_file_path']):
        return send_file(run['output_file_path'], as_attachment=True)

    if fmt == 'pdf':
        payload = {
            'run_id': run['run_id'],
            'status': run.get('status'),
            'started_at': str(run.get('started_at')),
        }
        return app.response_class(
            response=json.dumps(payload, indent=2),
            status=200,
            mimetype='application/json',
            headers={'Content-Disposition': f"attachment; filename=report-{report_id}.json"},
        )

    lines = ["run_id,status,started_at", f"{run['run_id']},{run.get('status')},{run.get('started_at')}"]
    return app.response_class(
        response="\n".join(lines) + "\n",
        status=200,
        mimetype='text/csv',
        headers={'Content-Disposition': f"attachment; filename=report-{report_id}.csv"},
    )


@app.route('/api/metrics/summary', methods=['GET'])
def metrics_summary():
    rows = _query_rows(
        """
        SELECT
            SUM(CASE WHEN status='matched' THEN 1 ELSE 0 END) AS matched,
            SUM(CASE WHEN status='unmatched' THEN 1 ELSE 0 END) AS unmatched,
            SUM(CASE WHEN status IN ('difference','manual_review') THEN 1 ELSE 0 END) AS suspense
        FROM reconciliation_results
        """
    )
    matched = int(rows[0]['matched'] or 0) if rows else 0
    unmatched = int(rows[0]['unmatched'] or 0) if rows else 0
    suspense = int(rows[0]['suspense'] or 0) if rows else 0

    value_rows = _query_rows(
        """
        SELECT COALESCE(SUM(bs.amount), 0) AS reconciled_value
        FROM reconciliation_results rr
        JOIN bank_statements bs ON rr.bank_statement_id = bs.statement_id
        WHERE rr.status = 'matched'
        """
    )
    reconciled_value = float(value_rows[0]['reconciled_value'] or 0) if value_rows else 0.0

    return jsonify({
        'matched': matched,
        'unmatched': unmatched,
        'suspense': suspense,
        'reconciledValue': reconciled_value,
    })


@app.route('/api/activity/recent', methods=['GET'])
def activity_recent():
    rows = _query_rows(
        "SELECT action, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10"
    )
    items = []
    for r in rows:
        items.append({
            'status': 'success',
            'message': str(r.get('action') or '').replace('_', ' ').title(),
            'timeAgo': _time_ago(r.get('created_at')),
        })
    return jsonify(items)


def _get_user_preferences(user_id):
    pref = _query_rows(
        "SELECT details FROM audit_logs WHERE user_id=%s AND action='user_preferences_updated' ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    if not pref:
        return {}
    try:
        details = pref[0].get('details')
        if isinstance(details, str):
            return json.loads(details)
        return details or {}
    except Exception:
        return {}


@app.route('/api/user/profile', methods=['GET', 'PUT'])
def user_profile():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'error': 'No user available'}), 404

    if request.method == 'PUT':
        data = request.get_json() or {}
        updates = []
        params = []
        if data.get('fullName') is not None:
            updates.append('full_name=%s')
            params.append(data.get('fullName'))
        if data.get('email') is not None:
            updates.append('email=%s')
            params.append(data.get('email'))

        if updates:
            _execute_update(
                f"UPDATE users SET {', '.join(updates)} WHERE user_id=%s",
                tuple(params + [user_id]),
            )
        return jsonify({'success': True})

    rows = _query_rows(
        """
        SELECT u.user_id, u.username, u.full_name, u.email, u.status, u.mfa_enabled,
               r.role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        WHERE u.user_id=%s
        LIMIT 1
        """,
        (user_id,),
    )
    if not rows:
        return jsonify({'error': 'User not found'}), 404

    u = rows[0]
    branch = _query_rows(
        "SELECT branch FROM bank_statements WHERE uploaded_by=%s AND branch IS NOT NULL AND branch <> '' ORDER BY uploaded_at DESC LIMIT 1",
        (user_id,),
    )
    branch_name = branch[0]['branch'] if branch else ''

    return jsonify({
        'fullName': u.get('full_name') or u.get('username') or '',
        'name': u.get('full_name') or u.get('username') or '',
        'email': u.get('email') or '',
        'phone': '',
        'role': str(u.get('role_name') or '').replace('_', ' ').title(),
        'branchName': branch_name,
        'branchCode': '',
        'status': u.get('status') or 'inactive',
        'twoFAEnabled': bool(u.get('mfa_enabled')),
        'preferences': _get_user_preferences(user_id),
    })


@app.route('/api/user/change-password', methods=['POST'])
def user_change_password():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'error': 'No user available'}), 404

    body = request.get_json() or {}
    current_password = body.get('currentPassword') or ''
    new_password = body.get('newPassword') or ''
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password are required'}), 400

    row = _query_rows("SELECT password_hash FROM users WHERE user_id=%s LIMIT 1", (user_id,))
    if not row:
        return jsonify({'error': 'User not found'}), 404

    stored_hash = row[0].get('password_hash') or ''
    valid = False
    try:
        if stored_hash.startswith('$2b$'):
            valid = bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8'))
        else:
            valid = check_password_hash(stored_hash, current_password)
    except Exception:
        valid = False

    if not valid:
        return jsonify({'error': 'Current password is incorrect'}), 400

    _execute_update(
        "UPDATE users SET password_hash=%s, password_changed_at=NOW() WHERE user_id=%s",
        (generate_password_hash(new_password), user_id),
    )
    return jsonify({'success': True, 'message': 'Password updated'})


@app.route('/api/user/twofa/enable', methods=['POST'])
def user_enable_twofa():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'error': 'No user available'}), 404
    _execute_update("UPDATE users SET mfa_enabled=TRUE WHERE user_id=%s", (user_id,))
    return jsonify({'success': True})


@app.route('/api/user/twofa/disable', methods=['POST'])
def user_disable_twofa():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'error': 'No user available'}), 404
    _execute_update("UPDATE users SET mfa_enabled=FALSE WHERE user_id=%s", (user_id,))
    return jsonify({'success': True})


@app.route('/api/user/preferences', methods=['PUT'])
def user_preferences():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'error': 'No user available'}), 404
    data = request.get_json() or {}
    _execute_insert(
        "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)",
        (user_id, 'user_preferences_updated', json.dumps(data), request.remote_addr),
    )
    return jsonify({'success': True, 'preferences': data})


@app.route('/api/user/activity', methods=['GET'])
def user_activity():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'items': []})
    limit = max(1, min(50, int(request.args.get('limit', 5))))
    rows = _query_rows(
        "SELECT action, created_at FROM audit_logs WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit),
    )
    return jsonify({'items': [
        {
            'action': str(r.get('action') or '').replace('_', ' ').title(),
            'status': 'success',
            'date': r.get('created_at'),
        }
        for r in rows
    ]})


@app.route('/api/user/devices', methods=['GET'])
def user_devices():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'items': []})
    rows = _query_rows(
        """
        SELECT session_id, ip_address, user_agent, is_active, last_activity
        FROM user_sessions
        WHERE user_id=%s
        ORDER BY last_activity DESC
        LIMIT 10
        """,
        (user_id,),
    )
    return jsonify({'items': [
        {
            'name': (r.get('user_agent') or 'Unknown Device')[:64],
            'type': 'mobile' if 'Mobile' in str(r.get('user_agent') or '') else 'desktop',
            'ip': r.get('ip_address') or '',
            'location': 'Unknown',
            'current': bool(r.get('is_active')),
            'lastSeen': r.get('last_activity'),
        }
        for r in rows
    ]})


@app.route('/api/user/export', methods=['GET'])
def user_export():
    user_id = _resolve_user_id()
    if not user_id:
        return jsonify({'error': 'No user available'}), 404
    profile_rows = _query_rows(
        "SELECT user_id, username, full_name, email, status, mfa_enabled FROM users WHERE user_id=%s",
        (user_id,),
    )
    activity_rows = _query_rows(
        "SELECT action, created_at FROM audit_logs WHERE user_id=%s ORDER BY created_at DESC LIMIT 100",
        (user_id,),
    )
    payload = json.dumps({'profile': profile_rows[0] if profile_rows else {}, 'activity': activity_rows}, default=str, indent=2)
    return app.response_class(
        response=payload,
        status=200,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=profile-export.json'}
    )


@app.route('/api/mail/imbalance', methods=['GET'])
def mail_imbalance():
    row = _query_rows(
        """
        SELECT rr.status, rr.difference, rr.matched_at,
               bs.branch, bs.transaction_date AS bank_date, bs.amount AS bank_amount,
               ir.amount AS internal_amount
        FROM reconciliation_results rr
        LEFT JOIN bank_statements bs ON rr.bank_statement_id = bs.statement_id
        LEFT JOIN internal_records ir ON rr.internal_record_id = ir.record_id
        WHERE rr.status IN ('unmatched', 'difference', 'manual_review')
        ORDER BY rr.matched_at DESC
        LIMIT 1
        """
    )
    if not row:
        return jsonify({'error': 'No imbalance record found'}), 404

    r = row[0]
    amount = r.get('difference')
    if amount is None:
        amount = r.get('bank_amount') if r.get('bank_amount') is not None else r.get('internal_amount')

    return jsonify({
        'branch': {'id': '', 'name': r.get('branch') or '', 'managerName': ''},
        'date': r.get('bank_date') or r.get('matched_at'),
        'amount': float(amount or 0),
        'status': str(r.get('status') or '').title(),
        'cause': '',
        'correction': '',
    })


@app.route('/api/mail/recipients', methods=['GET'])
def mail_recipients():
    rows = _query_rows(
        """
        SELECT u.full_name, u.email, r.role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        WHERE u.status='active' AND u.email IS NOT NULL
        ORDER BY u.created_at DESC
        LIMIT 20
        """
    )
    return jsonify([
        {
            'name': r.get('full_name') or '',
            'email': r.get('email') or '',
            'role': str(r.get('role_name') or '').replace('_', ' ').title(),
            'primary': idx == 0,
        }
        for idx, r in enumerate(rows)
    ])


@app.route('/api/mail/recent', methods=['GET'])
def mail_recent():
    limit = max(1, min(50, int(request.args.get('limit', 5))))
    rows = _query_rows(
        """
        SELECT action, details, created_at
        FROM audit_logs
        WHERE action IN ('mail_sent', 'mail_template_saved', 'mail_scheduled')
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    items = []
    for r in rows:
        details = r.get('details')
        payload = {}
        if isinstance(details, str):
            try:
                payload = json.loads(details)
            except Exception:
                payload = {}
        items.append({
            'status': 'sent' if r.get('action') == 'mail_sent' else 'pending',
            'title': payload.get('subject') or str(r.get('action') or '').replace('_', ' ').title(),
            'subject': payload.get('subject') or '',
            'date': r.get('created_at'),
        })
    return jsonify(items)


def _log_mail_action(action, data):
    user_id = _resolve_user_id()
    if not user_id:
        return
    _execute_insert(
        "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)",
        (user_id, action, json.dumps(data), request.remote_addr),
    )


@app.route('/api/mail/send', methods=['POST'])
def mail_send():
    data = request.get_json() or {}
    _log_mail_action('mail_sent', data)
    return jsonify({'success': True, 'message': 'Mail sent'})


@app.route('/api/mail/template', methods=['POST'])
def mail_template():
    data = request.get_json() or {}
    _log_mail_action('mail_template_saved', data)
    return jsonify({'success': True, 'message': 'Template saved'})


@app.route('/api/mail/schedule', methods=['POST'])
def mail_schedule():
    data = request.get_json() or {}
    _log_mail_action('mail_scheduled', data)
    return jsonify({'success': True, 'message': 'Mail scheduled'})

@app.route('/api/reconciliation/download/<filename>', methods=['GET'])
@require_auth
def download_reconciliation_report(filename):
    """Download reconciliation report file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

# Audit routes
@app.route('/api/audit/logs', methods=['GET'])
@require_auth
@require_role('admin')
def get_audit_logs():
    """Get audit logs (Admin only)"""
    try:
        logs = audit_manager.get_audit_logs()
        return jsonify({'logs': logs})
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return jsonify({'error': 'Failed to fetch audit logs'}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request was invalid or cannot be served',
        'status': 400
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required',
        'status': 401
    }), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource',
        'status': 403
    }), 403

@app.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status': 404
    }), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'error': 'File Too Large',
        'message': f'File size exceeds the maximum allowed size of {app.config["MAX_CONTENT_LENGTH"] / (1024*1024):.1f}MB',
        'status': 413
    }), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred. Please try again later.',
        'status': 500
    }), 500

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        db = DatabaseManager()
        db.execute_query("SELECT 1")
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'active_tasks': len(processing_tasks),
            'database': 'connected',
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'database': 'disconnected'
        }), 503

# Endpoint to view parsed bank statements
@app.route('/api/bank-statements', methods=['GET'])
@require_auth
def get_bank_statements():
    try:
        statements = file_manager.get_bank_statements()
        return jsonify({'bank_statements': statements})
    except Exception as e:
        logger.error(f"Error fetching bank statements: {e}")
        return jsonify({'error': 'Failed to fetch bank statements'}), 500

# Endpoint to view parsed internal records
@app.route('/api/internal-records', methods=['GET'])
@require_auth
def get_internal_records():
    try:
        records = file_manager.get_internal_records()
        return jsonify({'internal_records': records})
    except Exception as e:
        logger.error(f"Error fetching internal records: {e}")
        return jsonify({'error': 'Failed to fetch internal records'}), 500

# Background worker for reconciliation processing
def background_worker():
    """Background worker to process reconciliation tasks"""
    while True:
        try:
            task = task_queue.get(timeout=1)
            process_reconciliation_task(task)
            task_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Background worker error: {str(e)}")

def process_reconciliation_task(task):
    """Background task to process reconciliation"""
    try:
        task.status = 'processing'
        task.start_time = datetime.utcnow()
        processing_tasks[task.task_id] = task
        
        # Update progress
        task.progress = 10
        
        # Validate files exist
        bank_file_path = task.files.get('bank_statement')
        internal_file_path = task.files.get('internal_record')
        
        if not bank_file_path or not internal_file_path:
            raise ValueError("Both bank statement and internal record files are required")
        
        if not os.path.exists(bank_file_path) or not os.path.exists(internal_file_path):
            raise ValueError("One or more uploaded files not found")
        
        task.progress = 20
        
        # Initialize reconciliation engine
        tolerance = task.config.get('tolerance', 0.00)
        enable_fuzzy = task.config.get('enable_fuzzy', False)
        
        engine = ReconciliationEngine(
            tolerance=float(tolerance),
            enable_fuzzy=bool(enable_fuzzy)
        )
        
        task.progress = 40
        
        # Perform reconciliation
        result = engine.reconcile_from_files(bank_file_path, internal_file_path)
        
        task.progress = 80
        
        # Save results
        output_filename = f"reconciliation_{task.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result.matched.to_excel(writer, sheet_name='Matched', index=False)
            result.unmatched.to_excel(writer, sheet_name='Unmatched', index=False)
            
            # Create summary sheet
            summary_df = pd.DataFrame([{
                'Metric': 'Total Bank Records',
                'Value': result.summary['bank_count']
            }, {
                'Metric': 'Total Internal Records', 
                'Value': result.summary['collection_count']
            }, {
                'Metric': 'Matched Records',
                'Value': result.summary['matched_count']
            }, {
                'Metric': 'Unmatched Records',
                'Value': result.summary['unmatched_count']
            }, {
                'Metric': 'Match Percentage',
                'Value': f"{result.summary['matched_percentage']}%"
            }])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        task.progress = 100
        task.status = 'completed'
        task.result = {
            'output_file': output_filename,
            'summary': result.summary,
            'matched_count': len(result.matched),
            'unmatched_count': len(result.unmatched),
            'download_url': f"/api/reconciliation/download/{output_filename}"
        }

        # Persist reconciliation results (summary and line items)
        try:
            try:
                from .database import DatabaseManager, reconciliation_manager
            except ImportError:
                from database import DatabaseManager, reconciliation_manager
            db = DatabaseManager()
            db.execute_update(
                "UPDATE reconciliation_runs SET status=%s, completed_at=NOW(), output_file_path=%s, matched_count=%s, unmatched_count=%s WHERE run_id=%s",
                ('completed', output_path, len(result.matched), len(result.unmatched), task.task_id)
            )

            # Insert matched rows (without FK IDs if unavailable)
            for _ in range(len(result.matched)):
                reconciliation_manager.save_reconciliation_result(
                    bank_statement_id=None,
                    internal_record_id=None,
                    status='matched',
                    difference=0.00,
                    tolerance=float(task.config.get('tolerance', 0.00)),
                    matched_by=int(task.user_id),
                    reconciliation_run_id=task.task_id
                )

            # Insert unmatched rows
            for _ in range(len(result.unmatched)):
                reconciliation_manager.save_reconciliation_result(
                    bank_statement_id=None,
                    internal_record_id=None,
                    status='unmatched',
                    difference=0.00,
                    tolerance=float(task.config.get('tolerance', 0.00)),
                    matched_by=int(task.user_id),
                    reconciliation_run_id=task.task_id
                )
        except Exception as e:
            logger.error(f"Failed to persist reconciliation results: {e}")
        
        # Log successful completion
        log_audit(task.user_id, 'reconciliation_completed', {
            'task_id': task.task_id,
            'summary': result.summary,
            'output_file': output_filename
        })
        
    except Exception as e:
        task.status = 'failed'
        task.error = str(e)
        task.end_time = datetime.utcnow()
        
        logger.error(f"Reconciliation task {task.task_id} failed: {str(e)}")
        
        # Log failure
        log_audit(task.user_id, 'reconciliation_failed', {
            'task_id': task.task_id,
            'error': str(e)
        })
        try:
            try:
                from .database import DatabaseManager
            except ImportError:
                from database import DatabaseManager
            db = DatabaseManager()
            db.execute_update(
                "UPDATE reconciliation_runs SET status=%s, error_message=%s, completed_at=NOW() WHERE run_id=%s",
                ('failed', str(e), task.task_id)
            )
        except Exception as persist_err:
            logger.error(f"Failed to mark run failed in DB: {persist_err}")
    
    finally:
        task.end_time = datetime.utcnow()
        processing_tasks[task.task_id] = task

# Start background worker
worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


