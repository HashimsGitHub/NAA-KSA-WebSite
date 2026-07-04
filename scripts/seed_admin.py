import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.repositories.user_repository import UserRepository
from api.shared.password_utils import hash_password


USERS = [
    {
        "email": "admin@nust-alumni.org",
        "password": "Admin@12345",
        "full_name": "NUST Alumni Admin",
        "role": "admin",
    },
    {
        "email": "contributor@nust-alumni.org",
        "password": "Contributor@12345",
        "full_name": "NUST Alumni Contributor",
        "role": "contributor",
    },
    {
        "email": "user@nust-alumni.org",
        "password": "User@12345",
        "full_name": "NUST Alumni User",
        "role": "alumni",
    },
]


def seed_user(repo: UserRepository, email: str, password: str, full_name: str, role: str):
    existing = repo.get_user_by_email(email)

    if existing:
        print(f"EXISTS  {email} role={existing.get('role')}")
        return

    repo.create_user(
        email=email,
        full_name=full_name,
        mobile="",
        role=role,
        status="approved",
        auth_method="password",
        password_hash=hash_password(password),
        linked_alumni_id="",
    )

    print(f"CREATED {email} role={role}")


def main():
    repo = UserRepository()

    for user in USERS:
        seed_user(
            repo=repo,
            email=user["email"],
            password=user["password"],
            full_name=user["full_name"],
            role=user["role"],
        )


if __name__ == "__main__":
    main()