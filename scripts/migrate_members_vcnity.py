#!/usr/bin/env python3
"""
Migrate VCNITY member data from legacy AlumniProfiles to MemberProfiles.

Scope:
- Only the configured COMMUNITY_ID partition is touched.
- AlumniProfiles is NOT deleted.
- UserAccounts is updated from:
    linked_alumni_id -> linked_member_id
    role alumni -> member
- Existing MemberProfiles rows are upserted, so the script is rerunnable.

Run from:
  ~/projects/vcnity

Usage:
  source .venv/bin/activate
  python scripts/migrate_members_vcnity.py
"""

import json
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "api" / "local.settings.json"

if not SETTINGS.exists():
    raise SystemExit(f"Cannot find {SETTINGS}")

values = json.loads(SETTINGS.read_text(encoding="utf-8"))["Values"]

connection_string = values["AZURE_STORAGE_CONNECTION_STRING"]
community_id = values.get("COMMUNITY_ID", "VCNITY-DEV")

if community_id == "NUST-KSA":
    raise SystemExit(
        "Refusing to migrate COMMUNITY_ID=NUST-KSA. "
        "Run this against VCNITY-DEV first."
    )

service = TableServiceClient.from_connection_string(connection_string)

LEGACY_TABLE = "AlumniProfiles"
MEMBER_TABLE = "MemberProfiles"
USER_TABLE = "UserAccounts"

try:
    service.create_table(MEMBER_TABLE)
except ResourceExistsError:
    pass

legacy = service.get_table_client(LEGACY_TABLE)
members = service.get_table_client(MEMBER_TABLE)
users = service.get_table_client(USER_TABLE)

legacy_rows = list(
    legacy.query_entities(
        query_filter="PartitionKey eq @p",
        parameters={"p": community_id},
    )
)

print(f"Community     : {community_id}")
print(f"Legacy rows   : {len(legacy_rows)}")
print(f"Target table  : {MEMBER_TABLE}")
print()

migrated = 0

for row in legacy_rows:
    old_id = str(row.get("alumni_id") or row.get("RowKey") or "").strip()

    if not old_id:
        print("[SKIP] row has no usable id")
        continue

    entity = dict(row)

    entity["PartitionKey"] = community_id
    entity["RowKey"] = old_id
    entity["member_id"] = old_id

    # Keep the old field temporarily for compatibility while Stage 1 is active.
    entity["alumni_id"] = old_id

    role = str(entity.get("role") or "").strip().lower()
    if role == "alumni":
        entity["role"] = "member"

    members.upsert_entity(entity)
    migrated += 1

    email = str(entity.get("email") or "").strip().lower()

    if email:
        try:
            user = dict(
                users.get_entity(
                    partition_key=community_id,
                    row_key=email,
                )
            )

            user["linked_member_id"] = old_id

            # Keep legacy field during compatibility stage.
            user["linked_alumni_id"] = old_id

            if str(user.get("role") or "").lower() == "alumni":
                user["role"] = "member"

            users.upsert_entity(user)

        except Exception as exc:
            print(f"[WARN] Could not update UserAccounts for {email}: {exc}")

    print(f"[ OK ] {old_id} -> MemberProfiles")

print()
print(f"Migrated {migrated} member profile(s).")
print("AlumniProfiles was left unchanged for rollback.")
