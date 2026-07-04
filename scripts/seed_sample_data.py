"""Seed one alumni profile, event and knowledge article for portal testing."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api"
UNIVERSITY_ID = "NUST-KSA"


def setting(key):
    if os.environ.get(key):
        return os.environ[key]
    path = API / "local.settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["Values"][key]


def client(table_name):
    service = TableServiceClient.from_connection_string(setting("AZURE_STORAGE_CONNECTION_STRING"))
    try:
        service.create_table(table_name)
    except ResourceExistsError:
        pass
    return service.get_table_client(table_name)


def upsert(table_name, entity):
    client(table_name).upsert_entity(entity)
    print(f"Seeded {table_name}: {entity.get('title') or entity.get('full_name')}")


def main():
    now = datetime.now(timezone.utc).isoformat()
    alumni_id = "sample-alumni-001"
    upsert("AlumniProfiles", {
        "PartitionKey": UNIVERSITY_ID, "RowKey": alumni_id, "alumni_id": alumni_id,
        "full_name": "Sample NUST Alumni", "email": "sample.alumni@nust.edu.pk",
        "graduation_year": "2010", "degree": "BS Computer Science", "department": "SEECS",
        "current_company": "Example Technologies", "current_position": "Cloud Architect",
        "city": "Riyadh", "country": "Saudi Arabia", "skills": "Azure, AI, Cybersecurity",
        "bio": "Sample profile used to test the alumni directory.", "status": "active", "visibility": "visible",
        "show_email": True, "show_mobile": False, "created_at": now, "updated_at": now,
    })
    event_id = "sample-event-001"
    upsert("Events", {
        "PartitionKey": UNIVERSITY_ID, "RowKey": event_id, "id": event_id,
        "title": "NUST KSA Alumni Meetup", "summary": "Public meetup for NUST alumni in KSA.",
        "body": "Join fellow alumni for networking and community updates.", "category": "event",
        "event_date": "2026-08-15", "status": "published", "created_at": now, "updated_at": now,
    })
    post_id = "sample-knowledge-001"
    upsert("BlogPosts", {
        "PartitionKey": UNIVERSITY_ID, "RowKey": post_id, "id": post_id,
        "title": "Welcome to the Knowledge Base", "summary": "Member-only article for logged-in readers.",
        "body": "This area is for alumni knowledge sharing, career advice and community updates.",
        "category": "knowledge", "status": "published", "created_at": now, "updated_at": now,
    })

if __name__ == "__main__":
    main()
