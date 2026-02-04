from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: Optional[int]
    username: str
    password_hash: str
    full_name: str
    email: str
    role_id: int
    role_name: Optional[str] = None
    status: str = 'active'
    mfa_enabled: bool = False
    mfa_required: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    password_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __repr__(self):
        """
        function allows you to give each object a string
         representation to recognize it for debugging purposes.
        """
        return f'<User {self.user_id, self.role_name, self.created_at}>'
