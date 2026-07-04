"""
==========================================================
NUST KSA Alumni Portal

Password Utility Functions

Author : Hashim Hilal
==========================================================
"""

import secrets
import string
import bcrypt


# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------
from shared.config import PASSWORD_POLICY

BCRYPT_ROUNDS = PASSWORD_POLICY["bcrypt_rounds"]
DEFAULT_TEMP_PASSWORD_LENGTH = PASSWORD_POLICY["min_length"]

# ----------------------------------------------------------
# Password Hashing
# ----------------------------------------------------------

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Returns a UTF-8 encoded hash suitable for storage.
    """

    if not password:
        raise ValueError("Password cannot be empty.")

    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)

    password_hash = bcrypt.hashpw(password_bytes, salt)

    return password_hash.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a stored bcrypt hash.
    """

    if not password:
        return False

    if not password_hash:
        return False

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


# ----------------------------------------------------------
# Temporary Password Generator
# ----------------------------------------------------------

def generate_temp_password(length: int = DEFAULT_TEMP_PASSWORD_LENGTH) -> str:
    """
    Generate a secure temporary password.

    The password contains:
    - Uppercase
    - Lowercase
    - Numbers
    - Symbols
    """

    if length < 10:
        raise ValueError("Minimum password length is 10.")

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%&*?"

    alphabet = lowercase + uppercase + digits + symbols

    while True:

        password = "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )

        if (
            any(c in lowercase for c in password)
            and any(c in uppercase for c in password)
            and any(c in digits for c in password)
            and any(c in symbols for c in password)
        ):
            return password


# ----------------------------------------------------------
# Password Strength Checker
# ----------------------------------------------------------

def password_strength(password: str) -> dict:
    """
    Basic password strength evaluation.

    Returns:
        {
            "score": 0-5,
            "strong": bool
        }
    """

    score = 0

    if len(password) >= 10:
        score += 1

    if any(c.islower() for c in password):
        score += 1

    if any(c.isupper() for c in password):
        score += 1

    if any(c.isdigit() for c in password):
        score += 1

    if any(c in "!@#$%&*?" for c in password):
        score += 1

    return {
        "score": score,
        "strong": score >= 4,
    }
