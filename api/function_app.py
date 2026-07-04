import json
from typing import Any, Dict, Iterable

import azure.functions as func

from api.repositories.alumni_repository import AlumniRepository
from api.repositories.content_repository import ContentRepository
from api.repositories.user_repository import UserRepository
from api.services.auth_service import AuthService
from api.services.media_service import MediaService
from api.shared.config import ROLE_ADMIN, ROLE_CONTRIBUTOR, STATUS_APPROVED
from api.shared.jwt_utils import extract_bearer_token, verify_token
from api.shared.password_utils import hash_password

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def json_response(payload: Dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(payload, default=str), status_code=status, mimetype="application/json")


def body(req: func.HttpRequest) -> Dict[str, Any]:
    try:
        return req.get_json()
    except ValueError:
        return {}


def current_user(req: func.HttpRequest) -> Dict:
    token = extract_bearer_token(req.headers.get("Authorization", ""))
    if not token:
        return {}
    return verify_token(token) or {}


def require_role(req: func.HttpRequest, allowed: Iterable[str]) -> Dict:
    user = current_user(req)
    if not user:
        raise PermissionError("Login required")
    if user.get("role") not in allowed:
        raise PermissionError("Role not allowed")
    return user


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
    token = extract_bearer_token(req.headers.get("Authorization", ""))
    if not token:
        return json_response({"success": False, "message": "Login required"}, 401)
    result = AuthService().get_current_user(token)
    return json_response(result, 200 if result.get("success") else 401)


@app.route(route="users", methods=["GET", "POST"])
def users(req: func.HttpRequest) -> func.HttpResponse:
    repo = UserRepository()
    if req.method == "GET":
        try:
            require_role(req, [ROLE_ADMIN])
            rows = repo.list_users()
            for row in rows:
                row.pop("password_hash", None)
                row.pop("PartitionKey", None)
                row.pop("RowKey", None)
            return json_response({"success": True, "data": rows})
        except PermissionError as e:
            return json_response({"success": False, "message": str(e)}, 403)

    data = body(req)
    try:
        require_role(req, [ROLE_ADMIN])
        user = repo.create_user(
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            mobile=data.get("mobile", ""),
            role=data.get("role", "alumni"),
            status=data.get("status", STATUS_APPROVED),
            password_hash=hash_password(data.get("password", "ChangeMe123!")),
            linked_alumni_id=data.get("linked_alumni_id", ""),
        )
        user.pop("password_hash", None)
        return json_response({"success": True, "data": user}, 201)
    except PermissionError as e:
        return json_response({"success": False, "message": str(e)}, 403)
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


@app.route(route="alumni", methods=["GET", "POST"])
def alumni(req: func.HttpRequest) -> func.HttpResponse:
    repo = AlumniRepository()
    if req.method == "GET":
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

    try:
        require_role(req, [ROLE_ADMIN])
        return json_response({"success": True, "data": repo.create_profile(body(req))}, 201)
    except PermissionError as e:
        return json_response({"success": False, "message": str(e)}, 403)
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
        return json_response({"success": False, "message": str(e)}, 403)
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


def content_endpoint(req: func.HttpRequest, table_key: str, allowed_create_roles) -> func.HttpResponse:
    repo = ContentRepository(table_key)
    if req.method == "GET":
        category = req.params.get("category", "")
        return json_response({"success": True, "data": repo.list(published_only=True, category=category)})
    try:
        user = require_role(req, allowed_create_roles)
        return json_response({"success": True, "data": repo.create(body(req), user.get("sub", ""))}, 201)
    except PermissionError as e:
        return json_response({"success": False, "message": str(e)}, 403)
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)


@app.route(route="blogs", methods=["GET", "POST"])
def blogs(req: func.HttpRequest) -> func.HttpResponse:
    return content_endpoint(req, "blogs", [ROLE_ADMIN, ROLE_CONTRIBUTOR])


@app.route(route="events", methods=["GET", "POST"])
def events(req: func.HttpRequest) -> func.HttpResponse:
    return content_endpoint(req, "events", [ROLE_ADMIN, ROLE_CONTRIBUTOR])


@app.route(route="media/upload", methods=["POST"])
def media_upload(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN, ROLE_CONTRIBUTOR, "alumni"])
        data = body(req)
        result = MediaService().upload_image_base64(
            data.get("target", "profile"),
            data.get("file_name", "upload.png"),
            data.get("content_base64", ""),
        )
        return json_response({"success": True, "data": result}, 201)
    except PermissionError as e:
        return json_response({"success": False, "message": str(e)}, 403)
    except Exception as e:
        return json_response({"success": False, "message": str(e)}, 400)
