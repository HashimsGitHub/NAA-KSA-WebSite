#!/usr/bin/env python3
import getpass
import json
import sys
from urllib import error, request

BASE_URL = "http://localhost:7071/api"


def api(method, path, data=None, session_id=None):
    url = f"{BASE_URL}{path}"
    body = None if data is None else json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if session_id:
        headers["X-Session-Id"] = session_id
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"success": False, "message": raw}
        return exc.code, payload


def must(status, payload, expected, label):
    if status != expected or not payload.get("success"):
        print(f"[FAIL] {label}: HTTP {status} - {payload}")
        sys.exit(1)
    print(f"[ OK ] {label}")
    return payload.get("data")


def login():
    print("VCNITY-DEV seed utility")
    print("-----------------------")
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")
    status, payload = api("POST", "/auth/login", {"email": email, "password": password})
    data = must(status, payload, 200, "Admin login")
    if data.get("user", {}).get("role") != "admin":
        raise SystemExit("[FAIL] Supplied account is not an admin.")
    return data["session_id"]


def seed_events(session_id):
    events = [
        {
            "id": "vcnity-dev-event-001",
            "title": "VCNITY Community Welcome Evening",
            "summary": "Meet local members and discover how to participate in the VCNITY community.",
            "description": "A relaxed community welcome evening for introductions, networking and an overview of current VCNITY activities.",
            "event_date": "2026-10-17",
            "venue": "Community Hall",
            "city": "Brisbane",
            "tags": "community,welcome,networking",
            "status": "published",
            "cover_image_url": "",
        },
        {
            "id": "vcnity-dev-event-002",
            "title": "Digital Safety for Community Groups",
            "summary": "A practical session on safer online participation for community organisations.",
            "description": "Explore practical approaches to account security, privacy, moderation and safer digital collaboration.",
            "event_date": "2026-11-07",
            "venue": "VCNITY Workshop Space",
            "city": "Brisbane",
            "tags": "cybersecurity,safety,community",
            "status": "published",
            "cover_image_url": "",
        },
        {
            "id": "vcnity-dev-event-003",
            "title": "Community Co-design Workshop",
            "summary": "Help shape future features and experiences for the VCNITY digital hub.",
            "description": "Members work together to identify needs, prioritise ideas and co-design improvements to the community platform.",
            "event_date": "2026-11-28",
            "venue": "Innovation Studio",
            "city": "Brisbane",
            "tags": "co-design,ux,community",
            "status": "published",
            "cover_image_url": "",
        },
    ]
    print("\nSeeding Events")
    for item in events:
        status, payload = api("POST", "/events", item, session_id)
        must(status, payload, 201, item["title"])


def seed_knowledge(session_id):
    articles = [
        {
            "id": "vcnity-dev-knowledge-001",
            "title": "Getting Started with VCNITY",
            "summary": "A short guide to the Member Directory, Events and Knowledge Hub.",
            "body": "Welcome to VCNITY. Use the Member Directory to connect with members, Events to discover community activities, and the Knowledge Hub to access shared resources.",
            "tags": "getting-started,community",
            "status": "published",
            "cover_image_url": "",
        },
        {
            "id": "vcnity-dev-knowledge-002",
            "title": "Safer Digital Participation",
            "summary": "Simple practices that support privacy, security and respectful online participation.",
            "body": "Use strong passwords, protect personal information, consider what information should be shared publicly, and report concerning behaviour to community administrators.",
            "tags": "safety,privacy,security",
            "status": "published",
            "cover_image_url": "",
        },
        {
            "id": "vcnity-dev-knowledge-003",
            "title": "Inclusive Community Collaboration",
            "summary": "Ways to make community activities easier for more people to participate in.",
            "body": "Use clear language, accessible formats, respectful communication and flexible participation options. Consider different abilities, language backgrounds and levels of digital confidence.",
            "tags": "accessibility,inclusion,collaboration",
            "status": "published",
            "cover_image_url": "",
        },
    ]
    print("\nSeeding Knowledge Hub")
    for item in articles:
        status, payload = api("POST", "/knowledge", item, session_id)
        must(status, payload, 201, item["title"])


def seed_members(session_id):
    members = [
        {
            "alumni_id": "vcnity-dev-member-001",
            "full_name": "Alex Morgan",
            "email": "alex.morgan@example.com",
            "mobile": "0400000101",
            "city": "Brisbane",
            "country": "Australia",
            "degree": "Community Member",
            "department": "Creative Communities",
            "graduation_year": "2026",
            "current_company": "River City Arts Collective",
            "current_position": "Community Coordinator",
            "industry": "Community Arts",
            "linkedin_url": "",
            "bio": "Interested in community-led creative programs and inclusive local events.",
            "skills": "community engagement,events,facilitation",
            "profile_image_url": "",
            "role": "alumni",
            "status": "active",
            "visibility": "visible",
            "show_email": True,
            "show_mobile": False,
        },
        {
            "alumni_id": "vcnity-dev-member-002",
            "full_name": "Priya Shah",
            "email": "priya.shah@example.com",
            "mobile": "0400000102",
            "city": "Brisbane",
            "country": "Australia",
            "degree": "Community Member",
            "department": "Digital Inclusion",
            "graduation_year": "2026",
            "current_company": "Neighbourhood Connect",
            "current_position": "Volunteer Lead",
            "industry": "Community Services",
            "linkedin_url": "",
            "bio": "Supports digital inclusion and community volunteering programs.",
            "skills": "digital inclusion,volunteering,training",
            "profile_image_url": "",
            "role": "alumni",
            "status": "active",
            "visibility": "visible",
            "show_email": True,
            "show_mobile": False,
        },
        {
            "alumni_id": "vcnity-dev-member-003",
            "full_name": "Daniel Kim",
            "email": "daniel.kim@example.com",
            "mobile": "0400000103",
            "city": "Ipswich",
            "country": "Australia",
            "degree": "Community Member",
            "department": "Technology",
            "graduation_year": "2026",
            "current_company": "Community Tech Lab",
            "current_position": "Technology Volunteer",
            "industry": "Technology",
            "linkedin_url": "",
            "bio": "Helps community groups use practical and accessible digital tools.",
            "skills": "technology,web,community support",
            "profile_image_url": "",
            "role": "alumni",
            "status": "active",
            "visibility": "visible",
            "show_email": True,
            "show_mobile": False,
        },
        {
            "alumni_id": "vcnity-dev-member-004",
            "full_name": "Amina Yusuf",
            "email": "amina.yusuf@example.com",
            "mobile": "0400000104",
            "city": "Logan",
            "country": "Australia",
            "degree": "Community Member",
            "department": "Multicultural Communities",
            "graduation_year": "2026",
            "current_company": "Community Voices Network",
            "current_position": "Program Volunteer",
            "industry": "Community Development",
            "linkedin_url": "",
            "bio": "Interested in multicultural participation, accessibility and peer support.",
            "skills": "community development,peer support,multicultural engagement",
            "profile_image_url": "",
            "role": "alumni",
            "status": "active",
            "visibility": "visible",
            "show_email": True,
            "show_mobile": False,
        },
    ]
    print("\nSeeding Community Members")
    for item in members:
        status, payload = api("POST", "/alumni", item, session_id)
        must(status, payload, 201, item["full_name"])


def main():
    session_id = login()
    seed_events(session_id)
    seed_knowledge(session_id)
    seed_members(session_id)
    print("\nSeed complete.")
    print("Refresh http://localhost:4280 to see the VCNITY-DEV sample data.")


if __name__ == "__main__":
    main()
