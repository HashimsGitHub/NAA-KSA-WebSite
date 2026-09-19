#!/usr/bin/env python3
"""Verify MemberProfiles migration against AlumniProfiles for COMMUNITY_ID."""

import json
from pathlib import Path
from azure.data.tables import TableServiceClient

ROOT = Path(__file__).resolve().parent.parent
values = json.loads(
    (ROOT / "api" / "local.settings.json").read_text(encoding="utf-8")
)["Values"]

service = TableServiceClient.from_connection_string(
    values["AZURE_STORAGE_CONNECTION_STRING"]
)
community = values.get("COMMUNITY_ID", "VCNITY-DEV")

def rows(table_name):
    table = service.get_table_client(table_name)
    return list(
        table.query_entities(
            query_filter="PartitionKey eq @p",
            parameters={"p": community},
        )
    )

legacy = rows("AlumniProfiles")
members = rows("MemberProfiles")
users = rows("UserAccounts")

legacy_ids = {
    str(x.get("alumni_id") or x.get("RowKey"))
    for x in legacy
}
member_ids = {
    str(x.get("member_id") or x.get("RowKey"))
    for x in members
}

print(f"Community           : {community}")
print(f"AlumniProfiles rows : {len(legacy)}")
print(f"MemberProfiles rows : {len(members)}")
print(f"UserAccounts rows   : {len(users)}")

missing = sorted(legacy_ids - member_ids)

if missing:
    print()
    print("FAILED - missing MemberProfiles IDs:")
    for item in missing:
        print(f"  - {item}")
    raise SystemExit(1)

legacy_roles = [
    x.get("email")
    for x in users
    if str(x.get("role") or "").lower() == "alumni"
]

if legacy_roles:
    print()
    print("WARNING - UserAccounts still using role=alumni:")
    for email in legacy_roles:
        print(f"  - {email}")
else:
    print("All migrated UserAccounts roles use member/admin/contributor.")

print()
print("Migration verification PASSED.")
