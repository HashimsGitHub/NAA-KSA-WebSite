"""
NUST KSA Alumni Portal
JWT Utility Functions
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import uuid4

import jwt

from shared.config import (
    APPLICATION_NAME,
    ENV_JWT_SECRET,
    SESSION_TIMEOUT_HOURS,
    get_env,
)


JWT_ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    secret = get_env(ENV_JWT_SECRET)

    if not secret:
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. "
            "Add it to local.settings.json for local development "
            "and Azure App Settings for production."
        )

    return secret


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(
    email: str,
    user_id: str,
    role: str,
    session_id: str,
    expires_in_hours: int = SESSION_TIMEOUT_HOURS,
) -> str:
    now = utc_now()
    expiry = now + timedelta(hours=expires_in_hours)

    payload = {
        "iss": APPLICATION_NAME,
        "sub": email.strip().lower(),
        "user_id": user_id,
        "role": role,
        "session_id": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
        "jti": str(uuid4()),
    }

    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict:
    return jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[JWT_ALGORITHM],
        issuer=APPLICATION_NAME,
    )


def verify_token(token: str) -> Optional[Dict]:
    try:
        return decode_token(token)
    except Exception as e:
        print(f"JWT verification failed: {type(e).__name__}: {e}")
        return None


def extract_bearer_token(authorization_header: str) -> Optional[str]:
    if not authorization_header:
        return None

    parts = authorization_header.strip().split()

    if len(parts) != 2:
        return None

    if parts[0].lower() != "bearer":
        return None

    return parts[1]
