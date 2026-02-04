from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AuditLog:
    log_id: Optional[int]
    user_id: Optional[int]
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    severity: str = 'info'
    created_at: Optional[datetime] = None

    def __repr__(self):
        """
        function allows you to give each object a string
         representation to recognize it for debugging purposes.
        """
        return f'<AuditLog {self.log_id, self.user_id, self.created_at}>'
