from dataclasses import asdict
from typing import List
try:
    from ..database import reconciliation_manager
    from ..models.reconciliation_result import ReconciliationResult
except ImportError:
    from database import reconciliation_manager
    from models.reconciliation_result import ReconciliationResult


class ReconciliationService:
    def results(self, run_id: str = None, limit: int = 100) -> List[dict]:
        rows = reconciliation_manager.get_reconciliation_results(run_id=run_id, limit=limit)
        return [asdict(ReconciliationResult(
            result_id=r.get('result_id'),
            reconciliation_run_id=r.get('reconciliation_run_id'),
            bank_statement_id=r.get('bank_statement_id'),
            internal_record_id=r.get('internal_record_id'),
            status=r.get('status'),
            difference=r.get('difference'),
            tolerance=r.get('tolerance'),
            matched_by=r.get('matched_by'),
            matched_at=r.get('matched_at'),
        )) for r in rows]

# Create instance
reconciliation_service = ReconciliationService()


