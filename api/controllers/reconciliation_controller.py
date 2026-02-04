from flask import Blueprint, request, jsonify, send_file, current_app
try:
    from ..middleware.auth import require_auth
except ImportError:
    from middleware.auth import require_auth
from datetime import datetime
import os
import pandas as pd

try:
    from ..services.file_service import file_service
    from ..services import reconciliation_service
    from ..database import reconciliation_manager, reconciliation_runs_manager, audit_manager
except ImportError:
    from services.file_service import file_service
    from services import reconciliation_service
    from database import reconciliation_manager, reconciliation_runs_manager, audit_manager
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from reconciliation_system_production import ReconciliationEngine
except ImportError:
    ReconciliationEngine = None

recon_bp = Blueprint('recon', __name__, url_prefix='/api/reconciliation')

@recon_bp.route('/start', methods=['POST'])
@require_auth
def start_reconciliation():
    data = request.get_json() or {}
    tolerance = data.get('tolerance', 0.00)
    try:
        bank_statements = [r for r in file_service.recent_bank_statements(limit=1000)]
        internal_records = [r for r in file_service.recent_internal_records(limit=1000)]
        if not bank_statements:
            return jsonify({
                'success': False,
                'error': 'No bank statement data available for reconciliation. Please upload a bank statement file first.'
            }), 400
        if not internal_records:
            return jsonify({
                'success': False,
                'error': 'No internal record data available for reconciliation. Please upload an internal record file first.'
            }), 400

        run_id = f"RECON_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create reconciliation run record
        config = {'tolerance': tolerance, 'enable_fuzzy': False}
        reconciliation_runs_manager.create_run(run_id, request.current_user['user_id'], tolerance, config)
        
        # Update run status to processing
        reconciliation_runs_manager.update_run_status(run_id, 'processing', 
            bank_file_count=len(bank_statements), 
            internal_file_count=len(internal_records),
            total_transactions=len(bank_statements) + len(internal_records)
        )
        
        bank_df = pd.DataFrame(bank_statements)
        internal_df = pd.DataFrame(internal_records)

        # Validate required columns
        required_bank_cols = {'statement_id', 'amount', 'description'}
        required_internal_cols = {'record_id', 'amount', 'narration'}
        missing_bank_cols = required_bank_cols - set(bank_df.columns)
        missing_internal_cols = required_internal_cols - set(internal_df.columns)
        if missing_bank_cols:
            reconciliation_runs_manager.update_run_status(run_id, 'failed', 
                error_message=f'Missing required columns in bank statement data: {", ".join(missing_bank_cols)}.')
            return jsonify({
                'success': False,
                'error': f'Missing required columns in bank statement data: {", ".join(missing_bank_cols)}.'
            }), 400
        if missing_internal_cols:
            reconciliation_runs_manager.update_run_status(run_id, 'failed', 
                error_message=f'Missing required columns in internal record data: {", ".join(missing_internal_cols)}.')
            return jsonify({
                'success': False,
                'error': f'Missing required columns in internal record data: {", ".join(missing_internal_cols)}.'
            }), 400

        if not ReconciliationEngine:
            reconciliation_runs_manager.update_run_status(run_id, 'failed', 
                error_message='ReconciliationEngine not available')
            return jsonify({
                'success': False,
                'error': 'Reconciliation engine not available'
            }), 500

        engine = ReconciliationEngine(tolerance=float(tolerance))
        try:
            result = engine.reconcile_from_dfs(bank_df, internal_df)
        except Exception as e:
            reconciliation_runs_manager.update_run_status(run_id, 'failed', 
                error_message=f'Error during reconciliation logic: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Error during reconciliation logic: {str(e)}',
                'suggestion': 'Check that your files have the correct columns and data format.'
            }), 400

        # Use statement_id and record_id directly from the result DataFrames
        try:
            matched_count = 0
            unmatched_count = 0
            
            for _, row in result.matched.iterrows():
                statement_id = row.get('statement_id', 0)
                record_id = row.get('record_id', 0)
                reconciliation_manager.save_reconciliation_result(
                    bank_statement_id=statement_id,
                    internal_record_id=record_id,
                    status='matched',
                    difference=0.00,
                    tolerance=tolerance,
                    matched_by=request.current_user['user_id'],
                    reconciliation_run_id=run_id
                )
                matched_count += 1

            for _, row in result.unmatched.iterrows():
                statement_id = row.get('statement_id', 0)
                reconciliation_manager.save_reconciliation_result(
                    bank_statement_id=statement_id,
                    internal_record_id=None,
                    status='unmatched',
                    difference=row.get('amount', 0.00),
                    tolerance=tolerance,
                    matched_by=request.current_user['user_id'],
                    reconciliation_run_id=run_id
                )
                unmatched_count += 1
                
            # Update run with final counts
            reconciliation_runs_manager.update_run_status(run_id, 'completed',
                matched_count=matched_count,
                unmatched_count=unmatched_count,
                completed_at=datetime.now()
            )
                
        except Exception as e:
            reconciliation_runs_manager.update_run_status(run_id, 'failed', 
                error_message=f'Error saving reconciliation results: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Error saving reconciliation results: {str(e)}',
                'suggestion': 'Check that your database is accessible and the schema is correct.'
            }), 500

        output_filename = f"reconciliation_{run_id}.xlsx"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        try:
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
                
            # Update run with output file path
            reconciliation_runs_manager.update_run_status(run_id, 'completed',
                output_file_path=output_path
            )
                
        except Exception as e:
            reconciliation_runs_manager.update_run_status(run_id, 'failed', 
                error_message=f'Error generating Excel report: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Error generating Excel report: {str(e)}',
                'suggestion': 'Check that the output folder is writable and has enough space.'
            }), 500

        try:
            audit_manager.log_action(request.current_user['user_id'], 'reconciliation_completed', None, request.remote_addr)
        except Exception:
            pass

        # Improved download/results UX
        summary_table = {
            'Total Bank Records': result.summary.get('bank_count', 0),
            'Total Internal Records': result.summary.get('collection_count', 0),
            'Matched': result.summary.get('matched_count', 0),
            'Unmatched': result.summary.get('unmatched_count', 0),
            'Match Rate (%)': result.summary.get('matched_percentage', 0),
        }
        response = {
            'success': True,
            'run_id': run_id,
            'status': 'completed',
            'summary': summary_table,
            'download_url': request.host_url.rstrip('/') + f"/api/reconciliation/download/{output_filename}",
            'download_instructions': 'Click the download_url to get your reconciliation Excel report. Open it to review matched and unmatched records.',
        }
        if summary_table['Matched'] == 0:
            response['message'] = 'Reconciliation completed, but no matches were found. Consider increasing the tolerance or reviewing your data.'
        elif summary_table['Match Rate (%)'] < 50:
            response['message'] = 'Reconciliation completed with low match rate. Review unmatched records for possible data issues.'
        else:
            response['message'] = 'Reconciliation completed successfully.'
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Reconciliation failed: {str(e)}',
            'suggestion': 'Check your uploaded files and try again. If the problem persists, contact support.'
        }), 500


@recon_bp.route('/download/<filename>', methods=['GET'])
@require_auth
def download_report(filename: str):
    file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, as_attachment=True)


