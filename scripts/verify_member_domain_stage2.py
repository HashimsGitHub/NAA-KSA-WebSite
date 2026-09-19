#!/usr/bin/env python3
import json
from pathlib import Path
from azure.data.tables import TableServiceClient

ROOT = Path(__file__).resolve().parent.parent
v = json.loads((ROOT/"api"/"local.settings.json").read_text())["Values"]
community = v.get("COMMUNITY_ID","VCNITY-DEV")
svc = TableServiceClient.from_connection_string(v["AZURE_STORAGE_CONNECTION_STRING"])

def rows(name):
    return list(svc.get_table_client(name).query_entities(query_filter="PartitionKey eq @p",parameters={"p":community}))

errors=[]
for r in rows("MemberProfiles"):
    if "alumni_id" in r: errors.append(f"{r['RowKey']}: alumni_id remains")
    if not r.get("member_id"): errors.append(f"{r['RowKey']}: member_id missing")
    if str(r.get("role") or "").lower()=="alumni": errors.append(f"{r['RowKey']}: alumni role remains")
for r in rows("UserAccounts"):
    if "linked_alumni_id" in r: errors.append(f"{r['RowKey']}: linked_alumni_id remains")
    if str(r.get("role") or "").lower()=="alumni": errors.append(f"{r['RowKey']}: alumni role remains")

if errors:
    print("\n".join("[FAIL] "+e for e in errors))
    raise SystemExit(1)
print("FINAL MEMBER DOMAIN VERIFICATION PASSED.")
