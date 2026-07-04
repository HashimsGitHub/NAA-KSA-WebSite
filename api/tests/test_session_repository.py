from repositories.session_repository import SessionRepository


repo = SessionRepository()

session = repo.create_session(
    email="test.alumni@example.com",
    user_id="test-user-id",
    role="alumni",
    status="approved",
)

print("Created session:")
print(session)

session_id = session["session_id"]

valid = repo.is_session_valid(session_id)
print(f"\nValid session: {valid}")

revoked = repo.revoke_session(session_id)
print(f"Revoked: {revoked}")

valid_after_revoke = repo.is_session_valid(session_id)
print(f"Valid after revoke: {valid_after_revoke}")

assert valid is True
assert revoked is True
assert valid_after_revoke is False

print("\nSUCCESS")
