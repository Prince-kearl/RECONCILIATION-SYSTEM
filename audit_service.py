from dataclasses import asdict
from typing import List
try:
    from api.database import audit_manager
    from api.models.audit_log import AuditLog
except ImportError:
    try:
        from ..database import audit_manager
        from ..models.audit_log import AuditLog
    except ImportError:
        from database import audit_manager
        from models.audit_log import AuditLog


class AuditService:
    def recent(self, limit: int = 100) -> List[dict]:
        rows = audit_manager.get_audit_logs(limit)
        return [asdict(AuditLog(
            log_id=r.get('log_id'),
            user_id=r.get('user_id'),
            action=r.get('action'),
            details=r.get('details'),
            ip_address=r.get('ip_address'),
            created_at=r.get('created_at'),
        )) for r in rows]


