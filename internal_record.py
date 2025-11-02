from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class InternalRecord:
    record_id: Optional[int]
    transaction_date: datetime
    reference: str
    narration: Optional[str] = None
    amount: Optional[float] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    transaction_type: Optional[str] = None
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
        return f'<InternalRecord {self.record_id, self.reference, self.created_at}>'
