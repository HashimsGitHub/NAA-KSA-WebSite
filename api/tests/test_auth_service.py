from api.repositories.user_repository import UserRepository
from api.services.auth_service import AuthService
from api.shared.password_utils import hash_password


users = UserRepository()
auth = AuthService()

email = "auth.test@example.com"
password = "StrongPass123!"

existing = users.get_user_by_email(email)
if existing:
    users.delete_user(email)

password_hash = hash_password(password)

user = users.create_user(
    email=email,
    full_name="Auth Test User",
    mobile="+966500000001",
    role="alumni",
    status="approved",
    auth_method="password",
    password_hash=password_hash,
)

print("User created:")
print(user)

login_result = auth.login_with_password(
    email=email,
    password=password,
    ip_address="127.0.0.1",
    user_agent="test-runner",
)

print("\nLogin result:")
print(login_result)

assert login_result["success"] is True

token = login_result["data"]["token"]
session_id = login_result["data"]["session_id"]

validate_result = auth.validate_token(token)

print("\nValidate token result:")
print(validate_result)

assert validate_result["success"] is True

wrong_login = auth.login_with_password(
    email=email,
    password="WrongPassword123!",
)

print("\nWrong password result:")
print(wrong_login)

assert wrong_login["success"] is False

change_result = auth.change_password(
    email=email,
    old_password=password,
    new_password="NewStrongPass123!",
)

print("\nChange password result:")
print(change_result)

assert change_result["success"] is True

new_login = auth.login_with_password(
    email=email,
    password="NewStrongPass123!",
)

print("\nNew password login result:")
print(new_login)

assert new_login["success"] is True

reset_result = auth.reset_password_by_admin(
    email=email,
    admin_email="admin@nustksa.org",
)

print("\nAdmin reset result:")
print(reset_result)

assert reset_result["success"] is True
assert "temporary_password" in reset_result["data"]

logout_result = auth.logout(session_id)

print("\nLogout result:")
print(logout_result)

assert logout_result["success"] is True

users.delete_user(email)

print("\nSUCCESS")