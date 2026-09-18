import json
import getpass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import bcrypt
from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient


def utc_now_text():
    return datetime.now(timezone.utc).isoformat()


# local.settings.json is inside ../api
settings_path = Path(__file__).resolve().parent.parent / "api" / "local.settings.json"

if not settings_path.exists():
    raise SystemExit(f"Cannot find settings file: {settings_path}")

settings = json.loads(settings_path.read_text(encoding="utf-8"))
values = settings["Values"]

connection_string = values["AZURE_STORAGE_CONNECTION_STRING"]
community_id = values.get("COMMUNITY_ID", "VCNITY-DEV")

print()
print("VCNITY Development Admin Setup")
print("------------------------------")
print(f"Community: {community_id}")
print()

email = input("Admin email: ").strip().lower()
full_name = input("Admin full name: ").strip()
password = getpass.getpass("Admin password: ")
confirm_password = getpass.getpass("Confirm password: ")

if not email:
    raise SystemExit("Email is required.")

if not full_name:
    raise SystemExit("Full name is required.")

if len(password) < 10:
    raise SystemExit("Password must contain at least 10 characters.")

if password != confirm_password:
    raise SystemExit("Passwords do not match.")

password_hash = bcrypt.hashpw(
    password.encode("utf-8"),
    bcrypt.gensalt(rounds=12),
).decode("utf-8")

service = TableServiceClient.from_connection_string(connection_string)

try:
    service.create_table("UserAccounts")
except ResourceExistsError:
    pass

table = service.get_table_client("UserAccounts")

# Check whether the account already exists
existing = None

try:
    existing = table.get_entity(
        partition_key=community_id,
        row_key=email,
    )
except Exception:
    pass

entity = {
    "PartitionKey": community_id,
    "RowKey": email,
    "user_id": (
        existing.get("user_id")
        if existing
        else str(uuid4())
    ),
    "email": email,
    "full_name": full_name,
    "role": "admin",
    "status": "approved",
    "auth_method": "password",
    "password_hash": password_hash,
    "password_reset_required": False,
    "created_at": (
        existing.get("created_at")
        if existing
        else utc_now_text()
    ),
    "updated_at": utc_now_text(),
}

table.upsert_entity(entity)

print()
print("VCNITY admin account created successfully.")
print("-------------------------------------------")
print(f"Community : {community_id}")
print(f"Email     : {email}")
print(f"Name      : {full_name}")
print("Role      : admin")
print("Status    : approved")
print()
