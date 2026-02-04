from typing import Optional, List
from dataclasses import asdict
try:
    from ..database import user_manager
    from ..models.user import User
except ImportError:
    from database import user_manager
    from models.user import User


class UserService:
    def get_by_username(self, username: str) -> Optional[User]:
        row = user_manager.get_user_by_username(username)
        if not row:
            return None
        return User(
            user_id=row.get('user_id'),
            username=row.get('username'),
            password_hash=row.get('password_hash'),
            full_name=row.get('full_name'),
            email=row.get('email'),
            role_id=row.get('role_id'),
            role_name=row.get('role_name'),
            status=row.get('status'),
            last_login=row.get('last_login'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    def get_all(self) -> List[dict]:
        rows = user_manager.get_all_users()
        return [asdict(User(
            user_id=r.get('user_id'),
            username=r.get('username'),
            password_hash=r.get('password_hash'),
            full_name=r.get('full_name'),
            email=r.get('email'),
            role_id=r.get('role_id'),
            role_name=r.get('role_name'),
            status=r.get('status'),
            last_login=r.get('last_login'),
            created_at=r.get('created_at'),
            updated_at=r.get('updated_at'),
        )) for r in rows]


