"""Seed one alumni profile, one public event, and one knowledge post.

Run from project root after setting AZURE_STORAGE_CONNECTION_STRING
or after creating api/local.settings.json.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "api"
sys.path.insert(0, str(API_ROOT))
sys.path.insert(0, str(ROOT))

from repositories.alumni_repository import AlumniRepository
from repositories.content_repository import ContentRepository


def main():
    alumni = AlumniRepository()
    events = ContentRepository("events")
    knowledge = ContentRepository("blogs")

    existing = alumni.search_public_profiles(name="Sample Alumni")
    if existing:
        print("Sample alumni already exists")
    else:
        created = alumni.create_profile(
            {
                "full_name": "Sample Alumni",
                "email": "sample.alumni@example.com",
                "city": "Riyadh",
                "country": "Saudi Arabia",
                "degree": "BS Computer Science",
                "department": "Computer Science",
                "graduation_year": "2015",
                "current_company": "Example Company",
                "current_position": "Cloud Architect",
                "skills": "Azure, Python, AI",
                "visibility": "visible",
                "status": "active",
            }
        )
        print(f"Created alumni: {created['alumni_id']}")

    events.create(
        {
            "title": "NUST KSA Alumni Meetup",
            "summary": "Public meetup for NUST alumni in KSA.",
            "body": "Join fellow alumni for networking and community updates.",
            "event_date": "2026-08-15",
            "city": "Riyadh",
            "category": "event",
            "status": "published",
        },
        created_by="admin@nust-alumni.org",
    )
    print("Created sample event")

    knowledge.create(
        {
            "title": "How to update your alumni profile",
            "summary": "A short guide for keeping your alumni profile current.",
            "body": "Login, search your profile, and contact the admin if changes are required.",
            "category": "knowledge",
            "status": "published",
        },
        created_by="admin@nust-alumni.org",
    )
    print("Created sample knowledge post")


if __name__ == "__main__":
    main()
