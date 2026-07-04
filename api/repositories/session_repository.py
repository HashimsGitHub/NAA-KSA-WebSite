from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import uuid4

from azure.core.exceptions import ResourceNotFoundError

from api.shared.storage_client import StorageClient


UNIVERSITY_ID = "NUST-KSA"
SESSION_TABLE = "Sessions"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_expiry(hours: int = 8) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


class SessionRepository:
    def __init__(self):
        self.storage = StorageClient()
        self.table = self.storage.table(SESSION_TABLE)

    def create_session(
        self,
        email: str,
        user_id: str,
        role: str,
        status: str,
        ip_address: str = "",
        user_agent: str = "",
        expires_in_hours: int = 8,
    ) -> Dict:
        session_id = str(uuid4())

        entity = {
            "PartitionKey": UNIVERSITY_ID,
            "RowKey": session_id,
            "session_id": session_id,
            "email": email.strip().lower(),
            "user_id": user_id,
            "role": role,
            "status": status,
            "created_at": utc_now(),
            "expires_at": utc_expiry(expires_in_hours),
            "revoked": False,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        self.table.create_entity(entity=entity)
        return entity

    def get_session(self, session_id: str) -> Optional[Dict]:
        try:
            return dict(
                self.table.get_entity(
                    partition_key=UNIVERSITY_ID,
                    row_key=session_id,
                )
            )
        except ResourceNotFoundError:
            return None

    def revoke_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)

        if not session:
            return False

        session["revoked"] = True
        session["revoked_at"] = utc_now()

        self.table.upsert_entity(entity=session)
        return True

    def is_session_valid(self, session_id: str) -> bool:
        session = self.get_session(session_id)

        if not session:
            return False

        if session.get("revoked", False):
            return False

        if session.get("status") != "approved":
            return False

        expires_at = datetime.fromisoformat(session["expires_at"])

        return datetime.now(timezone.utc) < expires_at