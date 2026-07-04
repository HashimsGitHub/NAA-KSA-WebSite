import json
from typing import Any, Dict, Iterable, Optional

import azure.functions as func

from repositories.alumni_repository import AlumniRepository
from repositories.content_repository import ContentRepository
from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from services.auth_service import AuthService
from services.media_service import MediaService
from shared.config import ROLE_ADMIN, ROLE_ALUMNI, ROLE_CONTRIBUTOR, STATUS_APPROVED
from shared.password_utils import hash_password

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

def json_response(payload: Dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(payload, default=str), status_code=status, mimetype="application/json")


def body(req: func.HttpRequest) -> Dict[str, Any]:
    try:
        return req.get_json()
    except ValueError:
        return {}


def _safe_user(user: Dict) -> Dict:
    safe = dict(user or {})
    safe.pop("password_hash", None)
    safe.pop("PartitionKey", None)
    safe.pop("RowKey", None)
    return safe


def _session_id_from_request(req: func.HttpRequest) -> str:
    # Preferred KISS auth header used by the frontend.
    session_id = (
        req.headers.get("X-Session-Id")
        or req.headers.get("x-session-id")
        or req.params.get("session_id")
        or ""
    ).strip()

    if session_id:
        return session_id

    # Backward-compatible support for Authorization: Session <id> or Bearer <id>.
    auth_header = req.headers.get("Authorization") or req.headers.get("authorization") or ""
    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() in {"session", "bearer"}:
        return parts[1].strip()

    return ""


def current_user(req: func.HttpRequest) -> Dict:
    session_id = _session_id_from_request(req)
    if not session_id:
        return {}

    sessions = SessionRepository()
    if not sessions.is_session_valid(session_id):
        return {}

    session = sessions.get_session(session_id)
    if not session:
        return {}

    user = UserRepository().get_user_by_email(session.get("email", ""))
    if not user or user.get("status") != STATUS_APPROVED:
        return {}

    safe = _safe_user(user)
    safe["sub"] = safe.get("email", session.get("email", ""))
    safe["session_id"] = session_id
    safe["role"] = safe.get("role", session.get("role", ""))
    safe["user_id"] = safe.get("user_id", session.get("user_id", ""))
    return safe


def require_login(req: func.HttpRequest) -> Dict:
    user = current_user(req)
    if not user:
        raise PermissionError("Login required")
    return user


def require_role(req: func.HttpRequest, allowed: Iterable[str]) -> Dict:
    user = require_login(req)
    if user.get("role") not in allowed:
        raise PermissionError("Role not allowed")
    return user


def forbidden(message: str, login_required: bool = False) -> func.HttpResponse:
    return json_response({"success": False, "message": message}, 401 if login_required else 403)


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return json_response({"success": True, "message": "NUST Alumni API is running"})


@app.route(route="auth/login", methods=["POST"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    data = body(req)
    result = AuthService().login_with_password(data.get("email", ""), data.get("password", ""))
    return json_response(result, 200 if result.get("success") else 401)


@app.route(route="auth/me", methods=["GET"])
def me(req: func.HttpRequest) -> func.HttpResponse:
    user = current_user(req)
    if not user:
        return json_response({"success": False, "message": "Login required", "data": None}, 401)
    return json_response({"success": True, "message": "Current user retrieved.", "data": user})


@app.route(route="users", methods=["GET", "POST"])
def users(req: func.HttpRequest) -> func.HttpResponse:
    repo = UserRepository()
    try:
        require_role(req, [ROLE_ADMIN])
        if req.method == "GET":
            rows = repo.list_users()
            for row in rows:
                row.pop("password_hash", None)
                row.pop("PartitionKey", None)
                row.pop("RowKey", None)
            return json_response({"success": True, "data": rows})

        data = body(req)
        user = repo.create_user(
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            mobile=data.get("mobile", ""),
            role=data.get("role", ROLE_ALUMNI),
            status=data.get("status", STATUS_APPROVED),
            password_hash=hash_password(data.get("password", "ChangeMe123!")),
            linked_alumni_id=data.get("linked_alumni_id", ""),
        )
        user.pop("password_hash", None)
        return json_response({"success": True, "data": user}, 201)
    except PermissionError as e:
        return forbidden(str(e), str(e) == "Login required")
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


@app.route(route="alumni", methods=["GET", "POST"])
def alumni(req: func.HttpRequest) -> func.HttpResponse:
    repo = AlumniRepository()
    try:
        if req.method == "GET":
            require_login(req)
            params = req.params
            rows = repo.search_public_profiles(
                name=params.get("name", ""),
                city=params.get("city", ""),
                country=params.get("country", ""),
                degree=params.get("degree", ""),
                department=params.get("department", ""),
                graduation_year=params.get("graduation_year", ""),
                company=params.get("company", ""),
                industry=params.get("industry", ""),
                skills=params.get("skills", ""),
            )
            return json_response({"success": True, "data": rows})

        require_role(req, [ROLE_ADMIN])
        return json_response({"success": True, "data": repo.create_profile(body(req))}, 201)
    except PermissionError as e:
        return forbidden(str(e), str(e) == "Login required")
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


@app.route(route="alumni/{alumni_id}", methods=["PUT", "DELETE"])
def alumni_item(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN])
        repo = AlumniRepository()
        alumni_id = req.route_params.get("alumni_id")
        if req.method == "DELETE":
            return json_response({"success": repo.delete_profile(alumni_id)})
        return json_response({"success": True, "data": repo.update_profile(alumni_id, body(req))})
    except PermissionError as e:
        return forbidden(str(e), str(e) == "Login required")
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


def content_endpoint(
    req: func.HttpRequest,
    table_key: str,
    allowed_create_roles: Iterable[str],
    public_read: bool = False,
    default_category: Optional[str] = None,
) -> func.HttpResponse:
    repo = ContentRepository(table_key)
    try:
        if req.method == "GET":
            if not public_read:
                require_login(req)
            category = req.params.get("category", default_category or "")
            return json_response({"success": True, "data": repo.list(published_only=True, category=category)})

        user = require_role(req, allowed_create_roles)
        payload = body(req)
        if default_category and not payload.get("category"):
            payload["category"] = default_category
        return json_response({"success": True, "data": repo.create(payload, user.get("sub", ""))}, 201)
    except PermissionError as e:
        return forbidden(str(e), str(e) == "Login required")
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


@app.route(route="events", methods=["GET", "POST"])
def events(req: func.HttpRequest) -> func.HttpResponse:
    # Public GET. Create still requires admin/contributor.
    return content_endpoint(req, "events", [ROLE_ADMIN, ROLE_CONTRIBUTOR], public_read=True, default_category="event")


@app.route(route="knowledge", methods=["GET", "POST"])
def knowledge(req: func.HttpRequest) -> func.HttpResponse:
    # Knowledge Base requires login even for reading.
    return content_endpoint(req, "blogs", [ROLE_ADMIN, ROLE_CONTRIBUTOR], public_read=False, default_category="knowledge")


@app.route(route="blogs", methods=["GET", "POST"])
def blogs(req: func.HttpRequest) -> func.HttpResponse:
    # Backward-compatible alias. Blogs are treated as Knowledge Base and require login.
    return knowledge(req)


@app.route(route="media/upload", methods=["POST"])
def media_upload(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN, ROLE_CONTRIBUTOR, ROLE_ALUMNI])
        data = body(req)
        result = MediaService().upload_image_base64(
            data.get("target", "profile"),
            data.get("file_name", "upload.png"),
            data.get("content_base64", ""),
        )
        return json_response({"success": True, "data": result}, 201)
    except PermissionError as e:
        return forbidden(str(e), str(e) == "Login required")
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)
