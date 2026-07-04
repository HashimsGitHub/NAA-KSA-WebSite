from typing import Dict

from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from shared.config import STATUS_APPROVED
from shared.password_utils import (
    verify_password,
    hash_password,
    generate_temp_password,
)
from shared.response_utils import success_response, error_response


class AuthService:
    def __init__(self):
        self.users = UserRepository()
        self.sessions = SessionRepository()

    def login_with_password(
        self,
        email: str,
        password: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Dict:
        email = email.strip().lower()

        user = self.users.get_user_by_email(email)

        if not user:
            return error_response("Invalid email or password.")

        if user.get("status") != STATUS_APPROVED:
            return error_response(
                "Account is not approved.",
                [f"Current status: {user.get('status')}"],
            )

        if not verify_password(password, user.get("password_hash", "")):
            return error_response("Invalid email or password.")

        session = self.sessions.create_session(
            email=user["email"],
            user_id=user["user_id"],
            role=user["role"],
            status=user["status"],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.users.update_last_login(email)

        safe_user = self._safe_user(user)

        return success_response(
            "Login successful.",
            {
                "token": session["session_id"],
                "session_id": session["session_id"],
                "user": safe_user,
            },
        )

    def logout(self, session_id: str) -> Dict:
        revoked = self.sessions.revoke_session(session_id)

        if not revoked:
            return error_response("Session not found.")

        return success_response("Logout successful.")

    def validate_session(self, session_id: str) -> Dict:
        session_id = (session_id or "").strip()

        if not session_id:
            return error_response("Session is required.")

        if not self.sessions.is_session_valid(session_id):
            return error_response("Session is invalid or expired.")

        session = self.sessions.get_session(session_id)
        if not session:
            return error_response("Session not found.")

        user = self.users.get_user_by_email(session.get("email", ""))

        if not user:
            return error_response("User not found.")

        if user.get("status") != STATUS_APPROVED:
            return error_response("User account is not approved.")

        return success_response(
            "Session is valid.",
            {
                "session": session,
                "user": self._safe_user(user),
            },
        )

    def validate_token(self, token: str) -> Dict:
        # Backward-compatible name. In the KISS prototype, token == session_id.
        return self.validate_session(token)

    def change_password(
        self,
        email: str,
        old_password: str,
        new_password: str,
    ) -> Dict:
        email = email.strip().lower()

        user = self.users.get_user_by_email(email)

        if not user:
            return error_response("User not found.")

        if not verify_password(old_password, user.get("password_hash", "")):
            return error_response("Current password is incorrect.")

        new_hash = hash_password(new_password)

        self.users.set_password_hash(
            email=email,
            password_hash=new_hash,
            password_reset_required=False,
        )

        return success_response("Password changed successfully.")

    def reset_password_by_admin(
        self,
        email: str,
        admin_email: str,
    ) -> Dict:
        email = email.strip().lower()

        user = self.users.get_user_by_email(email)

        if not user:
            return error_response("User not found.")

        temp_password = generate_temp_password()
        temp_hash = hash_password(temp_password)

        self.users.set_password_hash(
            email=email,
            password_hash=temp_hash,
            password_reset_required=True,
        )

        return success_response(
            "Temporary password generated.",
            {
                "email": email,
                "temporary_password": temp_password,
                "reset_by": admin_email.strip().lower(),
            },
        )

    def get_current_user_by_session(self, session_id: str) -> Dict:
        result = self.validate_session(session_id)

        if not result["success"]:
            return result

        return success_response(
            "Current user retrieved.",
            result["data"]["user"],
        )

    def get_current_user(self, token: str) -> Dict:
        # Backward-compatible name. In the KISS prototype, token == session_id.
        return self.get_current_user_by_session(token)

    def _safe_user(self, user: Dict) -> Dict:
        safe = dict(user)

        safe.pop("password_hash", None)
        safe.pop("PartitionKey", None)
        safe.pop("RowKey", None)

        return safe
