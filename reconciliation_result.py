from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ReconciliationResult:
    result_id: Optional[int]
    reconciliation_run_id: str
    bank_statement_id: Optional[int] = None
    internal_record_id: Optional[int] = None
    status: str = 'unmatched'
    difference: Optional[float] = 0.00
    tolerance: Optional[float] = 0.00
    match_confidence: Optional[float] = 0.00
    match_criteria: Optional[str] = None
    matched_by: Optional[int] = None
    matched_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __repr__(self):
        """
        function allows you to give each object a string
         representation to recognize it for debugging purposes.
        """
        return f'<ReconciliationResult {self.result_id, self.status, self.reconciliation_run_id}>'
