from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: str
    email: str
    full_name: str
    mobile: str = ""
    role: str = "alumni"
    status: str = "pending"
    auth_method: str = "password"
    linked_alumni_id: str = ""
    password_reset_required: bool = False
    created_at: str = ""
    approved_by: str = ""
    approved_at: str = ""
    last_login_at: str = ""
    updated_at: Optional[str] = None
