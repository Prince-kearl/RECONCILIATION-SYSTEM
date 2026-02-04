from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BankStatement:
    statement_id: Optional[int]
    transaction_date: datetime
    bank_ref: str
    description: Optional[str] = None
    amount: Optional[float] = None
    branch: Optional[str] = None
    uploaded_by: Optional[int] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __repr__(self):
        """
        function allows you to give each object a string
         representation to recognize it for debugging purposes.
        """
        return f'<BankStatement {self.statement_id, self.bank_ref, self.created_at}>'
