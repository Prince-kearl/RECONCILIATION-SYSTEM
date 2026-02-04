
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from flask import current_app as flask_current_app
import os
import uuid
import hashlib
import logging
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
try:
    from ..database import file_manager, audit_manager
    from ..middleware.auth import require_auth
except ImportError:
    from database import file_manager, audit_manager
    from middleware.auth import require_auth

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

def calculate_file_checksum(file_path):
    """Calculate MD5 checksum of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum: {e}")
        return None

def get_mime_type(filename):
    """Get MIME type based on file extension"""
    ext = filename.rsplit('.', 1)[1].lower()
    mime_types = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel'
    }
    return mime_types.get(ext, 'application/octet-stream')

@files_bp.route('/upload/bank-statement', methods=['POST'])
@require_auth
def upload_bank_statement():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV, XLS, XLSX allowed'}), 400

    # Generate file_id and secure filename
    file_id = str(uuid.uuid4())
    filename = secure_filename(f"bank_{file_id}_{file.filename}")
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Create file upload record
    success = file_manager.create_file_upload(file_id, request.current_user['user_id'], file.filename)
    if not success:
        return jsonify({'error': 'Failed to create file upload record'}), 500
    
    try:
        # Parse and save transactions from file
        ext = filename.split('.')[-1].lower()
        try:
            if ext == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Handle different column name variations for date
            date_col = None
            if 'date' in df.columns:
                date_col = 'date'
            elif 'TRN_DT' in df.columns:
                date_col = 'TRN_DT'
            elif 'transaction_date' in df.columns:
                date_col = 'transaction_date'
            elif 'trn_date' in df.columns:
                date_col = 'trn_date'
            elif 'Date' in df.columns:
                date_col = 'Date'
            
            # Handle different column name variations for amount
            amount_col = None
            if 'amount' in df.columns:
                amount_col = 'amount'
            elif 'DR' in df.columns and 'CR' in df.columns:
                # Handle separate debit/credit columns
                amount_col = 'DR_CR'  # Special marker
            elif 'Amount' in df.columns:
                amount_col = 'Amount'
            elif 'AMOUNT' in df.columns:
                amount_col = 'AMOUNT'
            
            # Validate that we found required columns
            if not date_col:
                return jsonify({'error': 'Missing required date column. Expected: date, TRN_DT, transaction_date, trn_date, or Date'}), 400
            
            if not amount_col:
                return jsonify({'error': 'Missing required amount column. Expected: amount, DR/CR, Amount, or AMOUNT'}), 400
            
            desc_col = 'description' if 'description' in df.columns else 'narration' if 'narration' in df.columns else 'DESCRPTN' if 'DESCRPTN' in df.columns else None
            account_col = 'account_number' if 'account_number' in df.columns else 'account' if 'account' in df.columns else 'AC_NO' if 'AC_NO' in df.columns else None
            
            records_saved = 0
            for _, row in df.iterrows():
                try:
                    # Parse date - handle different formats
                    date_value = row.get(date_col)
                    if pd.isna(date_value):
                        transaction_date = datetime.utcnow().date().isoformat()
                    else:
                        if isinstance(date_value, str):
                            try:
                                transaction_date = pd.to_datetime(date_value).date().isoformat()
                            except:
                                transaction_date = datetime.utcnow().date().isoformat()
                        else:
                            transaction_date = pd.to_datetime(date_value).date().isoformat()
                    
                    # Parse amount
                    if amount_col == 'DR_CR':
                        # Handle separate debit/credit columns
                        dr_value = row.get('DR', 0)
                        cr_value = row.get('CR', 0)
                        
                        # Convert to float, handling NaN values
                        try:
                            dr_amount = float(dr_value) if not pd.isna(dr_value) else 0.00
                        except:
                            dr_amount = 0.00
                            
                        try:
                            cr_amount = float(cr_value) if not pd.isna(cr_value) else 0.00
                        except:
                            cr_amount = 0.00
                        
                        # Use the non-zero amount (either debit or credit)
                        amount_value = dr_amount if dr_amount > 0 else cr_amount
                    else:
                        # Handle single amount column
                        amount_value = row.get(amount_col, 0)
                        if pd.isna(amount_value):
                            amount_value = 0.00
                        else:
                            try:
                                amount_value = float(amount_value)
                            except:
                                amount_value = 0.00

                    file_manager.save_bank_statement(
                        file_id=file_id,
                        transaction_date=transaction_date,
                        amount=amount_value,
                        description=row.get(desc_col, ''),
                        account_number=row.get(account_col) if account_col else None
                    )
                    records_saved += 1
                except Exception as row_error:
                    logger.error(f"Error processing row {records_saved}: {row_error}")
                    continue
            
            logger.info(f"Successfully parsed and saved {records_saved} bank statement records from {filename}")
            
        except Exception as e:
            logger.error(f"Failed to parse bank statement file: {e}")
            return jsonify({'error': f'File parsing failed: {str(e)}'}), 400

        import json
        audit_manager.log_action(request.current_user['user_id'], 'file_uploaded', json.dumps({
            'file_type': 'bank_statement',
            'filename': filename,
            'file_id': file_id,
            'records_count': records_saved
        }), request.remote_addr)

        return jsonify({
            'success': True,
            'upload_id': file_id,
            'filename': filename,
            'original_filename': file.filename,
            'records_count': records_saved,
            'status': 'processed',
            'uploaded_at': datetime.now().isoformat(),
            'message': 'Bank statement uploaded and processed successfully'
        })
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@files_bp.route('/upload/internal-record', methods=['POST'])
@require_auth
def upload_internal_record():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV, XLS, XLSX allowed'}), 400

    # Generate file_id and secure filename
    file_id = str(uuid.uuid4())
    filename = secure_filename(f"internal_{file_id}_{file.filename}")
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Create file upload record
    success = file_manager.create_file_upload(file_id, request.current_user['user_id'], file.filename)
    if not success:
        return jsonify({'error': 'Failed to create file upload record'}), 500
    
    try:
        # Parse and save transactions from file
        ext = filename.split('.')[-1].lower()
        try:
            if ext == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Handle different column name variations for date
            date_col = None
            if 'date' in df.columns:
                date_col = 'date'
            elif 'TRN_DT' in df.columns:
                date_col = 'TRN_DT'
            elif 'transaction_date' in df.columns:
                date_col = 'transaction_date'
            elif 'trn_date' in df.columns:
                date_col = 'trn_date'
            elif 'Date' in df.columns:
                date_col = 'Date'
            
            # Handle different column name variations for amount
            amount_col = None
            if 'amount' in df.columns:
                amount_col = 'amount'
            elif 'DR' in df.columns and 'CR' in df.columns:
                # Handle separate debit/credit columns
                amount_col = 'DR_CR'  # Special marker
            elif 'Amount' in df.columns:
                amount_col = 'Amount'
            elif 'AMOUNT' in df.columns:
                amount_col = 'AMOUNT'
            
            # Validate that we found required columns
            if not date_col:
                return jsonify({'error': 'Missing required date column. Expected: date, TRN_DT, transaction_date, trn_date, or Date'}), 400
            
            if not amount_col:
                return jsonify({'error': 'Missing required amount column. Expected: amount, DR/CR, Amount, or AMOUNT'}), 400
            
            ref_col = 'ref' if 'ref' in df.columns else 'reference' if 'reference' in df.columns else 'internal_ref'
            desc_col = 'description' if 'description' in df.columns else 'narration' if 'narration' in df.columns else 'DESCRPTN' if 'DESCRPTN' in df.columns else None
            
            records_saved = 0
            for _, row in df.iterrows():
                try:
                    # Parse date - handle different formats
                    date_value = row.get(date_col)
                    if pd.isna(date_value):
                        transaction_date = datetime.utcnow().date().isoformat()
                    else:
                        if isinstance(date_value, str):
                            try:
                                transaction_date = pd.to_datetime(date_value).date().isoformat()
                            except:
                                transaction_date = datetime.utcnow().date().isoformat()
                        else:
                            transaction_date = pd.to_datetime(date_value).date().isoformat()
                    
                    # Parse amount
                    if amount_col == 'DR_CR':
                        # Handle separate debit/credit columns
                        dr_value = row.get('DR', 0)
                        cr_value = row.get('CR', 0)
                        
                        # Convert to float, handling NaN values
                        try:
                            dr_amount = float(dr_value) if not pd.isna(dr_value) else 0.00
                        except:
                            dr_amount = 0.00
                            
                        try:
                            cr_amount = float(cr_value) if not pd.isna(cr_value) else 0.00
                        except:
                            cr_amount = 0.00
                        
                        # Use the non-zero amount (either debit or credit)
                        amount_value = dr_amount if dr_amount > 0 else cr_amount
                    else:
                        # Handle single amount column
                        amount_value = row.get(amount_col, 0)
                        if pd.isna(amount_value):
                            amount_value = 0.00
                        else:
                            try:
                                amount_value = float(amount_value)
                            except:
                                amount_value = 0.00

                    file_manager.save_internal_record(
                        file_id=file_id,
                        transaction_date=transaction_date,
                        amount=amount_value,
                        reference=row.get(ref_col, f"INT_{uuid.uuid4().hex[:8]}"),
                        description=row.get(desc_col, '')
                    )
                    records_saved += 1
                except Exception as row_error:
                    logger.error(f"Error processing row {records_saved}: {row_error}")
                    continue
            
            logger.info(f"Successfully parsed and saved {records_saved} internal record records from {filename}")
            
        except Exception as e:
            logger.error(f"Failed to parse internal record file: {e}")
            return jsonify({'error': f'File parsing failed: {str(e)}'}), 400

        import json
        audit_manager.log_action(request.current_user['user_id'], 'file_uploaded', json.dumps({
            'file_type': 'internal_record',
            'filename': filename,
            'file_id': file_id,
            'records_count': records_saved
        }), request.remote_addr)

        return jsonify({
            'success': True,
            'upload_id': file_id,
            'filename': filename,
            'original_filename': file.filename,
            'records_count': records_saved,
            'status': 'processed',
            'uploaded_at': datetime.now().isoformat(),
            'message': 'Internal record uploaded and processed successfully'
        })
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

# Alias route to support old frontend calling 'collection-report'
@files_bp.route('/upload/collection-report', methods=['POST'])
@require_auth
def upload_collection_report_alias():
    return upload_internal_record()

@files_bp.route('/uploads', methods=['GET'])
@require_auth
def get_file_uploads():
    """Get list of uploaded files with optional filtering"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Get user's role to determine access level
        user_role = request.current_user.get('role_name', 'viewer')
        
        if user_role in ['admin', 'finance_officer']:
            # Admin and finance officers can see all files
            files = file_manager.get_file_uploads_summary(limit=limit)
        else:
            # Other users can only see their own files - simplified for now
            files = file_manager.get_file_uploads_summary(limit=limit)
            # Filter by user_id if needed (would require additional query)
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files),
            'filters': {
                'limit': limit
            }
        })
    except Exception as e:
        logger.error(f"Error getting file uploads: {e}")
        return jsonify({'error': f'Failed to get file uploads: {str(e)}'}), 500

@files_bp.route('/uploads/<int:upload_id>', methods=['GET'])
@require_auth
def get_file_upload(upload_id):
    """Get details of a specific file upload"""
    try:
        file_upload = file_manager.get_file_upload(upload_id)
        
        if not file_upload:
            return jsonify({'error': 'File upload not found'}), 404
        
        # Check if user has access to this file
        user_role = request.current_user.get('role_name', 'viewer')
        if user_role not in ['admin', 'finance_officer'] and file_upload['uploaded_by'] != request.current_user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'file': file_upload
        })
    except Exception as e:
        logger.error(f"Error getting file upload {upload_id}: {e}")
        return jsonify({'error': f'Failed to get file upload: {str(e)}'}), 500

@files_bp.route('/uploads/<int:upload_id>/status', methods=['GET'])
@require_auth
def get_file_upload_status(upload_id):
    """Get status of a specific file upload"""
    try:
        file_upload = file_manager.get_file_upload(upload_id)
        
        if not file_upload:
            return jsonify({'error': 'File upload not found'}), 404
        
        # Check if user has access to this file
        user_role = request.current_user.get('role_name', 'viewer')
        if user_role not in ['admin', 'finance_officer'] and file_upload['uploaded_by'] != request.current_user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'status': file_upload['status'],
            'error_message': file_upload.get('error_message'),
            'records_count': file_upload.get('records_count', 0),
            'processed_at': file_upload.get('processed_at')
        })
    except Exception as e:
        logger.error(f"Error getting file upload status {upload_id}: {e}")
        return jsonify({'error': f'Failed to get file upload status: {str(e)}'}), 500

@files_bp.route('/status/summary', methods=['GET'])
@require_auth
def get_file_status_summary():
    """Get file upload status summary for the dashboard"""
    try:
        # Get latest files using the new methods
        latest_bank = file_manager.get_latest_bank_file()
        latest_internal = file_manager.get_latest_internal_file()
        
        # Get summary statistics
        all_files = file_manager.get_file_uploads_summary(limit=100)
        total_files = len(all_files)
        processed_files = len([f for f in all_files if f['status'] == 'processed'])
        error_files = len([f for f in all_files if f['status'] == 'error'])
        processing_files = len([f for f in all_files if f['status'] == 'processing'])
        
        return jsonify({
            'success': True,
            'summary': {
                'total_files': total_files,
                'processed_files': processed_files,
                'error_files': error_files,
                'processing_files': processing_files
            },
            'bank_statement': {
                'status': latest_bank['status'] if latest_bank else 'not_uploaded',
                'filename': latest_bank['filename'] if latest_bank else None,
                'uploaded_at': latest_bank['uploaded_at'] if latest_bank else None,
                'records_count': latest_bank.get('records_count', 0) if latest_bank else 0,
                'file_size': 0,  # Not available in current schema
                'error_message': None  # Not available in current schema
            },
            'internal_record': {
                'status': latest_internal['status'] if latest_internal else 'not_uploaded',
                'filename': latest_internal['filename'] if latest_internal else None,
                'uploaded_at': latest_internal['uploaded_at'] if latest_internal else None,
                'records_count': latest_internal.get('records_count', 0) if latest_internal else 0,
                'file_size': 0,  # Not available in current schema
                'error_message': None  # Not available in current schema
            },
            'recent_files': {
                'bank_statements': [f for f in all_files if f['file_type'] == 'bank_statement'][:5],
                'internal_records': [f for f in all_files if f['file_type'] == 'internal_record'][:5]
            }
        })
    except Exception as e:
        logger.error(f"Error getting file status summary: {e}")
        return jsonify({'error': f'Failed to get file status summary: {str(e)}'}), 500


