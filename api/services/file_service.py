from dataclasses import asdict
from typing import List
try:
    from ..database import file_manager
    from ..models.bank_statement import BankStatement
    from ..models.internal_record import InternalRecord
except ImportError:
    from database import file_manager
    from models.bank_statement import BankStatement
    from models.internal_record import InternalRecord


class FileService:
    def recent_bank_statements(self, limit: int = 100) -> List[dict]:
        rows = file_manager.get_bank_statements(limit)
        return [asdict(BankStatement(
            statement_id=r.get('statement_id'),
            transaction_date=r.get('transaction_date'),
            bank_ref=r.get('bank_ref'),
            description=r.get('description'),
            amount=r.get('amount'),
            branch=r.get('branch'),
            uploaded_by=r.get('uploaded_by'),
            file_name=r.get('file_name'),
            file_path=r.get('file_path'),
            uploaded_at=r.get('uploaded_at'),
        )) for r in rows]

    def recent_internal_records(self, limit: int = 100) -> List[dict]:
        rows = file_manager.get_internal_records(limit)
        return [asdict(InternalRecord(
            record_id=r.get('record_id'),
            transaction_date=r.get('transaction_date'),
            reference=r.get('reference'),
            narration=r.get('narration'),
            amount=r.get('amount'),
            department=r.get('department'),
            uploaded_by=r.get('uploaded_by'),
            file_name=r.get('file_name'),
            file_path=r.get('file_path'),
            uploaded_at=r.get('uploaded_at'),
        )) for r in rows]

# Create instance
file_service = FileService()


