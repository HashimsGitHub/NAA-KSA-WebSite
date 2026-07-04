"""Seed the three KISS portal users into Azure Table Storage."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import bcrypt
from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api"
UNIVERSITY_ID = "NUST-KSA"
TABLE_USERS = "UserAccounts"

USERS = [
    ("admin@nust-alumni.org", "Admin@12345", "NUST Alumni Admin", "admin"),
    ("contributor@nust-alumni.org", "Contributor@12345", "NUST Alumni Contributor", "contributor"),
    ("user@nust-alumni.org", "User@12345", "NUST Alumni Reader", "reader"),
]


def setting(key):
    if os.environ.get(key):
        return os.environ[key]
    path = API / "local.settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["Values"][key]


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def main():
    service = TableServiceClient.from_connection_string(setting("AZURE_STORAGE_CONNECTION_STRING"))
    try:
        service.create_table(TABLE_USERS)
    except ResourceExistsError:
        pass
    table = service.get_table_client(TABLE_USERS)
    now = datetime.now(timezone.utc).isoformat()
    for email, password, full_name, role in USERS:
        entity = {
            "PartitionKey": UNIVERSITY_ID,
            "RowKey": email,
            "user_id": str(uuid4()),
            "email": email,
            "full_name": full_name,
            "role": role,
            "status": "approved",
            "password_hash": hash_password(password),
            "created_at": now,
            "updated_at": now,
        }
        table.upsert_entity(entity)
        print(f"Seeded {email} / {role}")

if __name__ == "__main__":
    main()
