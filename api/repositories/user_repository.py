from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from azure.core.exceptions import ResourceNotFoundError

from api.shared.storage_client import StorageClient

from api.shared.config import TABLES

from api.shared.config import UNIVERSITY_ID

#UNIVERSITY_ID = "NUST-KSA"

USER_TABLE = TABLES["users"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserRepository:
    def __init__(self):
        self.storage = StorageClient()
        self.table = self.storage.table(USER_TABLE)

    def create_user(
        self,
        email: str,
        full_name: str,
        mobile: str = "",
        role: str = "alumni",
        status: str = "pending",
        auth_method: str = "password",
        password_hash: str = "",
        linked_alumni_id: str = "",
    ) -> Dict:
        email = normalize_email(email)

        entity = {
            "PartitionKey": UNIVERSITY_ID,
            "RowKey": email,
            "user_id": str(uuid4()),
            "email": email,
            "full_name": full_name.strip(),
            "mobile": mobile.strip(),
            "role": role,
            "status": status,
            "auth_method": auth_method,
            "password_hash": password_hash,
            "password_reset_required": False,
            "linked_alumni_id": linked_alumni_id,
            "created_at": utc_now(),
            "approved_by": "",
            "approved_at": "",
            "last_login_at": "",
        }

        self.table.create_entity(entity=entity)
        return entity

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        email = normalize_email(email)

        try:
            return dict(
                self.table.get_entity(
                    partition_key=UNIVERSITY_ID,
                    row_key=email,
                )
            )
        except ResourceNotFoundError:
            return None

    def update_user(self, email: str, updates: Dict) -> Dict:
        user = self.get_user_by_email(email)

        if not user:
            raise ValueError(f"User not found: {email}")

        protected_fields = {"PartitionKey", "RowKey", "user_id", "email", "created_at"}

        for key, value in updates.items():
            if key not in protected_fields:
                user[key] = value

        user["updated_at"] = utc_now()

        self.table.upsert_entity(entity=user)
        return user

    def approve_user(self, email: str, approved_by: str) -> Dict:
        return self.update_user(
            email,
            {
                "status": "approved",
                "approved_by": normalize_email(approved_by),
                "approved_at": utc_now(),
            },
        )

    def reject_user(self, email: str, reviewed_by: str, reason: str = "") -> Dict:
        return self.update_user(
            email,
            {
                "status": "rejected",
                "approved_by": normalize_email(reviewed_by),
                "approved_at": utc_now(),
                "admin_notes": reason,
            },
        )

    def suspend_user(self, email: str, suspended_by: str, reason: str = "") -> Dict:
        return self.update_user(
            email,
            {
                "status": "suspended",
                "approved_by": normalize_email(suspended_by),
                "admin_notes": reason,
            },
        )

    def set_password_hash(
        self,
        email: str,
        password_hash: str,
        password_reset_required: bool = False,
    ) -> Dict:
        return self.update_user(
            email,
            {
                "password_hash": password_hash,
                "password_reset_required": password_reset_required,
            },
        )

    def update_last_login(self, email: str) -> Dict:
        return self.update_user(
            email,
            {
                "last_login_at": utc_now(),
            },
        )

    def list_users(self) -> List[Dict]:
        entities = self.table.query_entities(
            query_filter="PartitionKey eq @partition",
            parameters={"partition": UNIVERSITY_ID},
        )
        return [dict(entity) for entity in entities]

    def list_pending_users(self) -> List[Dict]:
        users = self.list_users()
        return [user for user in users if user.get("status") == "pending"]

    def list_approved_users(self) -> List[Dict]:
        users = self.list_users()
        return [user for user in users if user.get("status") == "approved"]

    def delete_user(self, email: str) -> bool:
        email = normalize_email(email)

        try:
            self.table.delete_entity(
                partition_key=UNIVERSITY_ID,
                row_key=email,
            )
            return True
        except ResourceNotFoundError:
            return False