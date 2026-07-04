from api.repositories.alumni_repository import AlumniRepository


repo = AlumniRepository()

profile = repo.create_profile(
    {
        "full_name": "Test Alumni",
        "preferred_name": "Test",
        "email": "test.alumni@example.com",
        "mobile": "+966500000000",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "degree": "BS Computer Science",
        "department": "SEECS",
        "graduation_year": "2015",
        "current_company": "Example Company",
        "current_position": "Cloud Architect",
        "industry": "Technology",
        "linkedin_url": "https://www.linkedin.com/in/example",
        "skills": "Azure, Cloud, AI",
        "show_mobile": False,
        "show_email": False,
    }
)

print("Created:")
print(profile)

alumni_id = profile["alumni_id"]

updated = repo.update_profile(
    alumni_id,
    {
        "city": "Jeddah",
        "available_to_mentor": True,
    },
)

print("\nUpdated:")
print(updated)

results = repo.search_public_profiles(
    name="Test",
    city="Jeddah",
    skills="Azure",
)

print("\nSearch Results:")
print(results)

deleted = repo.delete_profile(alumni_id)

print(f"\nDeleted: {deleted}")
print("\nSUCCESS")