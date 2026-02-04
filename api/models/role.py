from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Role:
    role_id: Optional[int]
    role_name: str
    description: Optional[str] = None
    permissions: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    def __repr__(self):
        """
        function allows you to give each object a string
         representation to recognize it for debugging purposes.
        """
        return f'<Role {self.role_id, self.role_name, self.created_at}>'
