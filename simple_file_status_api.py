#!/usr/bin/env python3
"""
Simple file status API that works with existing database structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
from flask import Flask, jsonify, request
from functools import wraps
import jwt
import json

app = Flask(__name__)

# Simple JWT verification (you can enhance this)
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            # For now, just check if token exists (you can add proper JWT verification)
            if token and len(token) > 10:
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': 'Token verification failed'}), 401
    
    return decorated_function

@app.route('/api/files/status/summary', methods=['GET'])
@require_auth
def get_file_status_summary():
    """Get file status summary for the dashboard"""
    try:
        db = DatabaseManager()
        
        # Get file uploads from existing table
        file_uploads_query = """
            SELECT fu.*, u.username as uploaded_by_name
            FROM file_uploads fu
            JOIN users u ON fu.user_id = u.user_id
            ORDER BY fu.uploaded_at DESC
            LIMIT 10
        """
        file_uploads = db.execute_query(file_uploads_query)
        
        # Get bank statements count
        bank_count_query = "SELECT COUNT(*) as count FROM bank_statements"
        bank_count_result = db.execute_query(bank_count_query)
        bank_count = bank_count_result[0]['count'] if bank_count_result else 0
        
        # Get internal records count
        internal_count_query = "SELECT COUNT(*) as count FROM internal_records"
        internal_count_result = db.execute_query(internal_count_query)
        internal_count = internal_count_result[0]['count'] if internal_count_result else 0
        
        # Get latest bank statement
        latest_bank_query = """
            SELECT bs.*, u.username as uploaded_by_name
            FROM bank_statements bs
            JOIN users u ON bs.uploaded_by = u.user_id
            ORDER BY bs.uploaded_at DESC
            LIMIT 1
        """
        latest_bank_result = db.execute_query(latest_bank_query)
        latest_bank = latest_bank_result[0] if latest_bank_result else None
        
        # Get latest internal record
        latest_internal_query = """
            SELECT ir.*, u.username as uploaded_by_name
            FROM internal_records ir
            JOIN users u ON ir.uploaded_by = u.user_id
            ORDER BY ir.uploaded_at DESC
            LIMIT 1
        """
        latest_internal_result = db.execute_query(latest_internal_query)
        latest_internal = latest_internal_result[0] if latest_internal_result else None
        
        # Calculate summary
        total_files = len(file_uploads)
        processed_files = bank_count + internal_count
        
        return jsonify({
            'success': True,
            'summary': {
                'total_files': total_files,
                'processed_files': processed_files,
                'error_files': 0,
                'processing_files': 0
            },
            'bank_statement': {
                'status': 'processed' if latest_bank else 'not_uploaded',
                'filename': latest_bank['file_name'] if latest_bank else None,
                'uploaded_at': latest_bank['uploaded_at'].isoformat() if latest_bank and latest_bank['uploaded_at'] else None,
                'records_count': bank_count,
                'file_size': 0,  # Not available in current schema
                'error_message': None
            },
            'internal_record': {
                'status': 'processed' if latest_internal else 'not_uploaded',
                'filename': latest_internal['file_name'] if latest_internal else None,
                'uploaded_at': latest_internal['uploaded_at'].isoformat() if latest_internal and latest_internal['uploaded_at'] else None,
                'records_count': internal_count,
                'file_size': 0,  # Not available in current schema
                'error_message': None
            },
            'recent_files': {
                'bank_statements': [latest_bank] if latest_bank else [],
                'internal_records': [latest_internal] if latest_internal else []
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get file status summary: {str(e)}'}), 500

@app.route('/api/files/uploads', methods=['GET'])
@require_auth
def get_file_uploads():
    """Get list of uploaded files"""
    try:
        db = DatabaseManager()
        
        # Get file uploads
        file_uploads_query = """
            SELECT fu.*, u.username as uploaded_by_name
            FROM file_uploads fu
            JOIN users u ON fu.user_id = u.user_id
            ORDER BY fu.uploaded_at DESC
            LIMIT 50
        """
        file_uploads = db.execute_query(file_uploads_query)
        
        # Convert to expected format
        files = []
        for upload in file_uploads:
            files.append({
                'upload_id': upload['file_id'],
                'filename': upload['filename'],
                'original_filename': upload['filename'],
                'file_type': 'unknown',  # Not available in current schema
                'status': 'uploaded',     # Assume uploaded if in table
                'uploaded_at': upload['uploaded_at'].isoformat() if upload['uploaded_at'] else None,
                'uploaded_by_name': upload['uploaded_by_name'],
                'records_count': 0,      # Not available in current schema
                'file_size': 0           # Not available in current schema
            })
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files),
            'filters': {
                'type': None,
                'status': None,
                'limit': 50
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get file uploads: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting Simple File Status API")
    print("=" * 50)
    print("📡 API will be available at: http://localhost:5001")
    print("🔍 Test endpoints:")
    print("   GET http://localhost:5001/api/files/status/summary")
    print("   GET http://localhost:5001/api/files/uploads")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
