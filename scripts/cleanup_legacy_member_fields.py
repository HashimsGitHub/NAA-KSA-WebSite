#!/usr/bin/env python3
import json
from pathlib import Path
from azure.data.tables import TableServiceClient, UpdateMode

ROOT = Path(__file__).resolve().parent.parent
values = json.loads((ROOT/"api"/"local.settings.json").read_text())["Values"]
community = values.get("COMMUNITY_ID","VCNITY-DEV")
if community == "NUST-KSA":
    raise SystemExit("Refusing to clean NUST-KSA")

svc = TableServiceClient.from_connection_string(values["AZURE_STORAGE_CONNECTION_STRING"])

def get_rows(name):
    t = svc.get_table_client(name)
    rows = list(t.query_entities(query_filter="PartitionKey eq @p", parameters={"p":community}))
    return t, rows

members, mrows = get_rows("MemberProfiles")
users, urows = get_rows("UserAccounts")

mc = uc = 0
for r in mrows:
    e = dict(r); changed = False
    if "alumni_id" in e:
        e.pop("alumni_id", None); changed = True
    if str(e.get("role") or "").lower() == "alumni":
        e["role"] = "member"; changed = True
    if changed:
        members.upsert_entity(e, mode=UpdateMode.REPLACE); mc += 1

for r in urows:
    e = dict(r); changed = False
    if "linked_alumni_id" in e:
        e.pop("linked_alumni_id", None); changed = True
    if str(e.get("role") or "").lower() == "alumni":
        e["role"] = "member"; changed = True
    if changed:
        users.upsert_entity(e, mode=UpdateMode.REPLACE); uc += 1

print(f"Community: {community}")
print(f"MemberProfiles cleaned: {mc}")
print(f"UserAccounts cleaned: {uc}")
print("AlumniProfiles table left untouched.")
