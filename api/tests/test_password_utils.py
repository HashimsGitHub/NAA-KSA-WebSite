from api.shared.password_utils import (
    hash_password,
    verify_password,
    generate_temp_password,
    password_strength,
)

print("Generating password...")

password = generate_temp_password()

print(password)

strength = password_strength(password)

print(strength)

assert strength["strong"] is True

password_hash = hash_password(password)

print("\nPassword Hash:")

print(password_hash)

assert password_hash != password

assert verify_password(password, password_hash)

assert verify_password("WrongPassword", password_hash) is False

print("\nSUCCESS")