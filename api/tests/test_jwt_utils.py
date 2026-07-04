from api.shared.jwt_utils import (
    create_token,
    verify_token,
    extract_bearer_token,
)


token = create_token(
    email="test.alumni@example.com",
    user_id="test-user-id",
    role="alumni",
    session_id="test-session-id",
)

print("JWT Token:")
print(token)

payload = verify_token(token)

print("\nDecoded Payload:")
print(payload)

assert payload is not None
assert payload["sub"] == "test.alumni@example.com"
assert payload["role"] == "alumni"
assert payload["session_id"] == "test-session-id"

header = f"Bearer {token}"
extracted = extract_bearer_token(header)

assert extracted == token

print("\nSUCCESS")