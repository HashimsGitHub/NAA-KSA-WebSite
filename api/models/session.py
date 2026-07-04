from dataclasses import dataclass


@dataclass
class Session:
    session_id: str
    email: str
    user_id: str
    role: str
    status: str
    created_at: str
    expires_at: str
    revoked: bool = False
    ip_address: str = ""
    user_agent: str = ""
    revoked_at: str = ""