from api.repositories.user_repository import UserRepository


repo = UserRepository()

email = "test.alumni@example.com"

existing = repo.get_user_by_email(email)
if existing:
    repo.delete_user(email)

user = repo.create_user(
    email=email,
    full_name="Test Alumni",
    mobile="+966500000000",
    role="alumni",
    status="pending",
)

print("Created:")
print(user)

approved = repo.approve_user(email, approved_by="admin@nustksa.org")

print("\nApproved:")
print(approved)

pending = repo.list_pending_users()
approved_users = repo.list_approved_users()

print(f"\nPending users: {len(pending)}")
print(f"Approved users: {len(approved_users)}")

deleted = repo.delete_user(email)

print(f"\nDeleted: {deleted}")
print("\nSUCCESS")