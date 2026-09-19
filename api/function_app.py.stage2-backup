"""KISS backend for NUST KSA Alumni Portal.

One Azure Static Web Apps managed API file.
Storage: Azure Tables + Azure Blob Storage.
Auth: simple random Session ID stored in Azure Table.
"""

import base64
import json
import mimetypes
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

import azure.functions as func
import bcrypt
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, ContentSettings

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

COMMUNITY_ID = os.getenv("COMMUNITY_ID", "NUST-KSA")
SESSION_HOURS = 8

TABLE_USERS = "UserAccounts"
TABLE_SESSIONS = "Sessions"
TABLE_MEMBERS = "MemberProfiles"
TABLE_ALUMNI_LEGACY = "AlumniProfiles"  # Stage 1 compatibility only
TABLE_EVENTS = "Events"
TABLE_KNOWLEDGE = "BlogPosts"
BLOB_IMAGES = "images"
BLOB_SITE_IMAGES = "site-images"

ROLE_ADMIN = "admin"
ROLE_CONTRIBUTOR = "contributor"
ROLE_READER = "reader"
ROLE_MEMBER = "member"
ROLE_ALUMNI_LEGACY = "alumni"  # Stage 1 compatibility only
USER_ROLES = {
    ROLE_ADMIN,
    ROLE_CONTRIBUTOR,
    ROLE_MEMBER,
    ROLE_ALUMNI_LEGACY,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_text() -> str:
    return utc_now().isoformat()


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def normalize_email(email: str) -> str:
    return clean(email).lower()


def read_local_setting(key: str) -> Optional[str]:
    path = Path(__file__).resolve().parent / "local.settings.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data.get("Values", {}).get(key)
        return value if value else None
    except Exception:
        return None


def get_setting(key: str) -> str:
    value = os.environ.get(key) or read_local_setting(key)
    if not value:
        raise RuntimeError(f"Missing required setting: {key}")
    return value


def storage_connection() -> str:
    return get_setting("AZURE_STORAGE_CONNECTION_STRING")


_table_service: Optional[TableServiceClient] = None
_blob_service: Optional[BlobServiceClient] = None


def table_service() -> TableServiceClient:
    global _table_service
    if _table_service is None:
        _table_service = TableServiceClient.from_connection_string(storage_connection())
    return _table_service


def blob_service() -> BlobServiceClient:
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobServiceClient.from_connection_string(storage_connection())
    return _blob_service


def table(name: str):
    service = table_service()
    try:
        service.create_table(name)
    except ResourceExistsError:
        pass
    return service.get_table_client(name)


def json_response(payload: Dict[str, Any], status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, default=str),
        status_code=status,
        mimetype="application/json",
    )


def ok(data: Any = None, message: str = "OK", status: int = 200) -> func.HttpResponse:
    return json_response({"success": True, "message": message, "data": data if data is not None else []}, status)


def fail(message: str, status: int = 400) -> func.HttpResponse:
    return json_response({"success": False, "message": message, "data": None}, status)


def body(req: func.HttpRequest) -> Dict[str, Any]:
    try:
        return req.get_json()
    except ValueError:
        return {}


def remove_storage_keys(entity: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(entity)
    item.pop("PartitionKey", None)
    item.pop("RowKey", None)
    item.pop("password_hash", None)
    return item


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def get_user(email: str) -> Optional[Dict[str, Any]]:
    email = normalize_email(email)
    if not email:
        return None
    try:
        return dict(table(TABLE_USERS).get_entity(partition_key=COMMUNITY_ID, row_key=email))
    except ResourceNotFoundError:
        return None


def save_user(email: str, full_name: str, password: str, role: str = ROLE_READER, status: str = "approved") -> Dict[str, Any]:
    email = normalize_email(email)
    if not email or not password:
        raise ValueError("Email and password are required.")
    role = clean(role).lower() or ROLE_READER
    entity = {
        "PartitionKey": COMMUNITY_ID,
        "RowKey": email,
        "user_id": str(uuid4()),
        "email": email,
        "full_name": clean(full_name) or email,
        "role": role,
        "status": clean(status) or "approved",
        "password_hash": hash_password(password),
        "created_at": utc_now_text(),
        "updated_at": utc_now_text(),
    }
    table(TABLE_USERS).upsert_entity(entity)
    return entity


def normalize_user_role(value: Any) -> str:
    role = clean(value).lower()
    if role == ROLE_ALUMNI_LEGACY:
        return ROLE_MEMBER
    if role in {ROLE_ADMIN, ROLE_CONTRIBUTOR, ROLE_MEMBER}:
        return role
    return ROLE_MEMBER


def member_status_to_user_status(value: Any) -> str:
    status = clean(value).lower()
    if status in ("active", "approved", ""):
        return "approved"
    if status == "inactive":
        return "suspended"
    return status

def delete_sessions_for_email(
    email: str,
) -> None:

    email = normalize_email(email)

    if not email:
        return

    sessions_table = table(
        TABLE_SESSIONS
    )

    rows = sessions_table.query_entities(
        query_filter=(
            "PartitionKey eq @partition "
            "and email eq @email"
        ),
        parameters={
            "partition": COMMUNITY_ID,
            "email": email,
        },
    )

    for session in rows:
        try:
            sessions_table.delete_entity(
                partition_key=COMMUNITY_ID,
                row_key=session["RowKey"],
            )
        except ResourceNotFoundError:
            pass
        
def sync_member_user(
    alumni: Dict[str, Any],
    previous_email: str = "",
    previous_mobile: str = "",
) -> Optional[Dict[str, Any]]:

    email = normalize_email(alumni.get("email", ""))
    mobile = clean(alumni.get("mobile"))

    previous_email = normalize_email(previous_email)
    previous_mobile = clean(previous_mobile)

    if not email or not mobile:
        return None

    email_changed = bool(
        previous_email
        and previous_email != email
    )

    mobile_changed = bool(
        previous_mobile
        and previous_mobile != mobile
    )

    users_table = table(TABLE_USERS)

    # Preserve identity information from the old account if
    # the member's email/username has changed.
    old_user: Dict[str, Any] = {}

    if email_changed:
        try:
            old_user = dict(
                users_table.get_entity(
                    partition_key=COMMUNITY_ID,
                    row_key=previous_email,
                )
            )
        except ResourceNotFoundError:
            old_user = {}

    # There may already be an account using the new email.
    existing_new_user = get_user(email) or {}

    # Prefer the existing account at the new email.
    # Otherwise preserve the old account's identity fields.
    existing = existing_new_user or old_user

    entity = {
        **existing,

        "PartitionKey": COMMUNITY_ID,
        "RowKey": email,

        "user_id": (
            clean(existing.get("user_id"))
            or str(uuid4())
        ),

        "email": email,

        "full_name": (
            clean(alumni.get("full_name"))
            or clean(existing.get("full_name"))
            or email
        ),

        "mobile": mobile,

        "role": normalize_user_role(
            alumni.get("role")
        ),

        "status": member_status_to_user_status(
            alumni.get("status")
            or existing.get("status")
        ),

        "auth_method": "password",

        # Current VCNITY authentication strategy:
        # username = email
        # password = mobile number
        "password_hash": hash_password(mobile),

        "password_reset_required": False,

        "linked_member_id": clean(
            alumni.get("member_id")
            or existing.get("linked_alumni_id")
        ),

        "created_at": (
            clean(existing.get("created_at"))
            or utc_now_text()
        ),

        "updated_at": utc_now_text(),
    }

    # -------------------------------------------------
    # Save account under CURRENT email
    # -------------------------------------------------
    users_table.upsert_entity(entity)

    # -------------------------------------------------
    # Email changed:
    # remove OLD username/account and sessions
    # -------------------------------------------------
    if email_changed:
        try:
            users_table.delete_entity(
                partition_key=COMMUNITY_ID,
                row_key=previous_email,
            )
        except ResourceNotFoundError:
            pass

        delete_sessions_for_email(previous_email)

    # -------------------------------------------------
    # Mobile changed:
    # password changed, therefore invalidate any
    # sessions belonging to the current/new email.
    # -------------------------------------------------
    if mobile_changed:
        delete_sessions_for_email(email)

    return entity

def create_session(user: Dict[str, Any], req: func.HttpRequest) -> Dict[str, Any]:
    session_id = secrets.token_urlsafe(32)
    role = clean(user.get("role") or ROLE_MEMBER).lower()
    entity = {
        "PartitionKey": COMMUNITY_ID,
        "RowKey": session_id,
        "session_id": session_id,
        "email": normalize_email(user.get("email") or user.get("RowKey")),
        "user_id": clean(user.get("user_id")),
        "full_name": clean(user.get("full_name")),
        "role": role,
        "status": clean(user.get("status") or "approved"),
        "created_at": utc_now_text(),
        "expires_at": (utc_now() + timedelta(hours=SESSION_HOURS)).isoformat(),
        "revoked": False,
        "ip_address": req.headers.get("X-Forwarded-For", ""),
        "user_agent": req.headers.get("User-Agent", ""),
    }
    table(TABLE_SESSIONS).upsert_entity(entity)
    return entity


def session_id_from_req(req: func.HttpRequest) -> str:
    session_id = clean(req.headers.get("X-Session-Id") or req.headers.get("x-session-id"))
    if session_id:
        return session_id
    auth = clean(req.headers.get("Authorization") or req.headers.get("authorization"))
    if auth.lower().startswith("session "):
        return auth.split(" ", 1)[1].strip()
    return ""


def current_user(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    sid = session_id_from_req(req)
    if not sid:
        return None
    try:
        session = dict(table(TABLE_SESSIONS).get_entity(partition_key=COMMUNITY_ID, row_key=sid))
    except ResourceNotFoundError:
        return None
    if session.get("revoked"):
        return None
    if clean(session.get("status")) != "approved":
        return None
    try:
        expires = datetime.fromisoformat(clean(session.get("expires_at")))
        if utc_now() >= expires:
            return None
    except Exception:
        return None
    user = get_user(session.get("email", "")) or {}
    role = clean(user.get("role") or session.get("role") or ROLE_MEMBER).lower()
    return {
        "email": normalize_email(user.get("email") or session.get("email")),
        "user_id": clean(user.get("user_id") or session.get("user_id")),
        "full_name": clean(user.get("full_name") or session.get("full_name")),
        "role": role,
        "session_id": sid,
    }

def require_login(req: func.HttpRequest) -> Dict[str, Any]:
    user = current_user(req)
    if not user:
        raise PermissionError("Login required")
    return user


def require_role(req: func.HttpRequest, allowed: Iterable[str]) -> Dict[str, Any]:
    user = require_login(req)
    allowed_set = {r.lower() for r in allowed}
    role = user.get("role", "").lower()
    if role not in allowed_set:
        raise PermissionError("Role not allowed")
    return user


def list_table_rows(table_name: str) -> List[Dict[str, Any]]:
    rows = table(table_name).query_entities(
        query_filter="PartitionKey eq @partition",
        parameters={"partition": COMMUNITY_ID},
    )
    return [dict(row) for row in rows]


def contains(field: Any, value: str) -> bool:
    value = clean(value).lower()
    if not value:
        return True
    return value in clean(field).lower()


def public_member(profile: Dict[str, Any]) -> Dict[str, Any]:
    item = remove_storage_keys(profile)
    if not bool(item.get("show_email", True)):
        item["email"] = ""
    if not bool(item.get("show_mobile", False)):
        item["mobile"] = ""
    return item


def content_rows(table_name: str, category: str = "") -> List[Dict[str, Any]]:
    rows = [remove_storage_keys(row) for row in list_table_rows(table_name)]
    rows = [row for row in rows if clean(row.get("status") or "published") == "published"]
    if category:
        rows = [row for row in rows if clean(row.get("category")) in ("", category)]
    rows.sort(key=lambda x: clean(x.get("event_date") or x.get("created_at")), reverse=True)
    return rows


def get_table_item(table_name: str, item_id: str) -> Dict[str, Any]:
    item_id = clean(item_id)
    if not item_id:
        raise ValueError("Item id is required.")
    try:
        return dict(table(table_name).get_entity(partition_key=COMMUNITY_ID, row_key=item_id))
    except ResourceNotFoundError:
        raise ValueError("Item not found.")


def create_content(req: func.HttpRequest, table_name: str, category: str, user: Dict[str, Any]) -> Dict[str, Any]:
    data = body(req)
    item_id = clean(data.get("id")) or str(uuid4())
    entity = {
        "PartitionKey": COMMUNITY_ID,
        "RowKey": item_id,
        "id": item_id,
        "title": clean(data.get("title")),
        "summary": clean(data.get("summary")),
        "body": clean(data.get("body") or data.get("description")),
        "category": category,
        "tags": clean(data.get("tags")),
        "event_date": clean(data.get("event_date")),
        "venue": clean(data.get("venue")),
        "city": clean(data.get("city")),
        "cover_image_url": clean(data.get("cover_image_url")),
        "status": clean(data.get("status") or "published"),
        "created_by": user.get("email", ""),
        "created_at": utc_now_text(),
        "updated_at": utc_now_text(),
    }
    if not entity["title"]:
        raise ValueError("Title is required.")
    table(table_name).upsert_entity(entity)
    return remove_storage_keys(entity)


def update_content(req: func.HttpRequest, table_name: str, item_id: str, category: str) -> Dict[str, Any]:
    data = body(req)
    entity = get_table_item(table_name, item_id)
    editable = [
        "title",
        "summary",
        "body",
        "description",
        "tags",
        "event_date",
        "venue",
        "city",
        "cover_image_url",
        "status",
    ]
    for key in editable:
        if key in data:
            target = "body" if key == "description" else key
            entity[target] = clean(data.get(key))
    entity["category"] = category
    entity["updated_at"] = utc_now_text()
    if not clean(entity.get("title")):
        raise ValueError("Title is required.")
    table(table_name).upsert_entity(entity)
    return remove_storage_keys(entity)


def delete_item(table_name: str, item_id: str) -> None:
    item_id = clean(item_id)
    if not item_id:
        raise ValueError("Item id is required.")
    try:
        table(table_name).delete_entity(partition_key=COMMUNITY_ID, row_key=item_id)
    except ResourceNotFoundError:
        raise ValueError("Item not found.")


def upsert_member(
    data: Dict[str, Any],
    member_id: str = "",
) -> Dict[str, Any]:

    member_id = (
        clean(member_id or data.get("member_id") or data.get("alumni_id"))
        or str(uuid4())
    )

    # -------------------------------------------------
    # Load the EXISTING profile BEFORE changing anything.
    # This is critical for detecting email/mobile changes.
    # -------------------------------------------------
    existing: Dict[str, Any] = {}

    try:
        existing = get_table_item(
            TABLE_MEMBERS,
            member_id,
        )
    except ValueError:
        pass

    # Capture previous credentials BEFORE constructing
    # or saving the updated member profile.
    previous_email = normalize_email(
        existing.get("email", "")
    )

    previous_mobile = clean(
        existing.get("mobile", "")
    )

    # -------------------------------------------------
    # Build updated member entity
    # -------------------------------------------------
    entity = {
        **existing,

        "PartitionKey": COMMUNITY_ID,
        "RowKey": member_id,

        "member_id": member_id,
        "alumni_id": member_id,  # Stage 1 compatibility

        "full_name": clean(
            data.get(
                "full_name",
                existing.get("full_name", ""),
            )
        ),

        "email": normalize_email(
            data.get(
                "email",
                existing.get("email", ""),
            )
        ),

        "mobile": clean(
            data.get(
                "mobile",
                existing.get("mobile", ""),
            )
        ),

        "city": clean(
            data.get(
                "city",
                existing.get("city", ""),
            )
        ),

        "country": clean(
            data.get(
                "country",
                existing.get("country", ""),
            )
        ),

        "degree": clean(
            data.get(
                "degree",
                existing.get("degree", ""),
            )
        ),

        "department": clean(
            data.get(
                "department",
                existing.get("department", ""),
            )
        ),

        "graduation_year": clean(
            data.get(
                "graduation_year",
                existing.get("graduation_year", ""),
            )
        ),

        "current_company": clean(
            data.get(
                "current_company",
                existing.get("current_company", ""),
            )
        ),

        "current_position": clean(
            data.get(
                "current_position",
                existing.get("current_position", ""),
            )
        ),

        "industry": clean(
            data.get(
                "industry",
                existing.get("industry", ""),
            )
        ),

        "linkedin_url": clean(
            data.get(
                "linkedin_url",
                existing.get("linkedin_url", ""),
            )
        ),

        "bio": clean(
            data.get(
                "bio",
                existing.get("bio", ""),
            )
        ),

        "skills": clean(
            data.get(
                "skills",
                existing.get("skills", ""),
            )
        ),

        "profile_image_url": clean(
            data.get(
                "profile_image_url",
                existing.get("profile_image_url", ""),
            )
        ),

        "role": normalize_user_role(
            data.get(
                "role",
                existing.get(
                    "role",
                    ROLE_MEMBER,
                ),
            )
        ),

        "status": clean(
            data.get(
                "status",
                existing.get(
                    "status",
                    "active",
                ),
            )
            or "active"
        ),

        "visibility": clean(
            data.get(
                "visibility",
                existing.get(
                    "visibility",
                    "visible",
                ),
            )
            or "visible"
        ),

        "show_email": bool(
            data.get(
                "show_email",
                existing.get(
                    "show_email",
                    True,
                ),
            )
        ),

        "show_mobile": bool(
            data.get(
                "show_mobile",
                existing.get(
                    "show_mobile",
                    False,
                ),
            )
        ),

        "created_at": (
            clean(existing.get("created_at"))
            or utc_now_text()
        ),

        "updated_at": utc_now_text(),
    }

    if not entity["full_name"]:
        raise ValueError(
            "Full name is required."
        )

    if not entity["email"]:
        raise ValueError(
            "Email is required."
        )

    if not entity["mobile"]:
        raise ValueError(
            "Mobile number is required."
        )

    # -------------------------------------------------
    # Save updated member profile
    # -------------------------------------------------
    table(TABLE_MEMBERS).upsert_entity(entity)

    # -------------------------------------------------
    # Synchronise login account.
    #
    # IMPORTANT:
    # previous_email and previous_mobile were captured
    # before the profile was updated.
    # -------------------------------------------------
    sync_member_user(
        entity,
        previous_email=previous_email,
        previous_mobile=previous_mobile,
    )

    return public_member(entity)

def delete_member_and_user(member_id: str) -> None:
    member_id = clean(member_id)

    if not member_id:
        raise ValueError("Member id is required.")

    try:
        profile = dict(
            table(TABLE_MEMBERS).get_entity(
                partition_key=COMMUNITY_ID,
                row_key=member_id,
            )
        )
    except ResourceNotFoundError:
        raise ValueError("Member not found.")

    email = normalize_email(
        profile.get("email", "")
    )

    # Delete profile
    table(TABLE_MEMBERS).delete_entity(
        partition_key=COMMUNITY_ID,
        row_key=member_id,
    )

    # Delete login
    if email:
        try:
            table(TABLE_USERS).delete_entity(
                partition_key=COMMUNITY_ID,
                row_key=email,
            )
        except ResourceNotFoundError:
            pass

        # Delete sessions
        delete_sessions_for_email(email)

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return ok(
        {
            "version": "vcnity-dev-v1",
            "community_id": COMMUNITY_ID
        },
        "VCNITY Community Hub API is running"
    )


@app.route(route="register", methods=["POST"])
def register(req: func.HttpRequest) -> func.HttpResponse:
    return fail("Registration is disabled. Alumni accounts are managed through the member database import.", 410)



@app.route(route="auth/login", methods=["POST"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    data = body(req)
    user = get_user(data.get("email", ""))
    if not user or not verify_password(data.get("password", ""), clean(user.get("password_hash"))):
        return fail("Invalid email or password.", 401)
    if clean(user.get("status") or "approved") != "approved":
        return fail("User is not approved.", 403)
    session = create_session(user, req)
    safe_user = remove_storage_keys(user)
    return ok(
        {
            "session_id": session["session_id"],
            "user": safe_user,
        },
        "Login successful.",
    )


@app.route(route="auth/logout", methods=["POST"])
def logout(req: func.HttpRequest) -> func.HttpResponse:
    sid = session_id_from_req(req)
    if sid:
        try:
            t = table(TABLE_SESSIONS)
            session = dict(t.get_entity(partition_key=COMMUNITY_ID, row_key=sid))
            session["revoked"] = True
            session["revoked_at"] = utc_now_text()
            t.upsert_entity(session)
        except ResourceNotFoundError:
            pass
    return ok({}, "Logged out.")


@app.route(route="auth/me", methods=["GET"])
def session(req: func.HttpRequest) -> func.HttpResponse:
    user = current_user(req)
    if not user:
        return fail("Login required", 401)
    return ok(user, "Session active.")


@app.route(route="events", methods=["GET", "POST"])
def events(req: func.HttpRequest) -> func.HttpResponse:
    try:
        if req.method == "GET":
            return ok(content_rows(TABLE_EVENTS, "event"), "Events loaded.")
        user = require_role(req, [ROLE_ADMIN, ROLE_CONTRIBUTOR])
        return ok(create_content(req, TABLE_EVENTS, "event", user), "Event created.", 201)
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="events/{item_id}", methods=["PUT", "DELETE"])
def event_item(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN, ROLE_CONTRIBUTOR])
        item_id = req.route_params.get("item_id", "")
        if req.method == "DELETE":
            delete_item(TABLE_EVENTS, item_id)
            return ok({}, "Event deleted.")
        return ok(update_content(req, TABLE_EVENTS, item_id, "event"), "Event updated.")
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="knowledge", methods=["GET", "POST"])
def knowledge(req: func.HttpRequest) -> func.HttpResponse:
    try:
        if req.method == "GET":
            require_login(req)
            return ok(content_rows(TABLE_KNOWLEDGE, "knowledge"), "Knowledge loaded.")
        user = require_role(req, [ROLE_ADMIN, ROLE_CONTRIBUTOR])
        return ok(create_content(req, TABLE_KNOWLEDGE, "knowledge", user), "Knowledge article created.", 201)
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="knowledge/{item_id}", methods=["PUT", "DELETE"])
def knowledge_item(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN, ROLE_CONTRIBUTOR])
        item_id = req.route_params.get("item_id", "")
        if req.method == "DELETE":
            delete_item(TABLE_KNOWLEDGE, item_id)
            return ok({}, "Knowledge article deleted.")
        return ok(update_content(req, TABLE_KNOWLEDGE, item_id, "knowledge"), "Knowledge article updated.")
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="members", methods=["GET", "POST"])
def members(req: func.HttpRequest) -> func.HttpResponse:
    try:
        if req.method == "GET":
            require_login(req)
            p = req.params
            rows = []
            for profile in list_table_rows(TABLE_MEMBERS):
                status = clean(profile.get("status") or "active")
                visibility = clean(profile.get("visibility") or "visible")
                if status not in ("", "active") or visibility not in ("", "visible"):
                    continue
                if not contains(profile.get("full_name"), p.get("name", "")):
                    continue
                if not contains(profile.get("city"), p.get("city", "")):
                    continue
                if not contains(profile.get("country"), p.get("country", "")):
                    continue
                if not contains(profile.get("degree"), p.get("degree", "")):
                    continue
                if not contains(profile.get("department"), p.get("department", "")):
                    continue
                if not contains(profile.get("graduation_year"), p.get("graduation_year", "")):
                    continue
                if not contains(profile.get("current_company"), p.get("company", "")):
                    continue
                if not contains(profile.get("skills"), p.get("skills", "")):
                    continue
                rows.append(public_member(profile))
            rows.sort(key=lambda x: clean(x.get("full_name")).lower())
            return ok(rows, "Members loaded.")

        require_role(req, [ROLE_ADMIN])
        return ok(upsert_member(body(req)), "Member profile saved.", 201)
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="members/{member_id}", methods=["PUT", "DELETE"])
def member_item(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN])

        member_id = req.route_params.get("member_id", "")

        if req.method == "DELETE":
            delete_member_and_user(member_id)
            return ok(
                {},
                "Member profile and linked account deleted."
            )

        return ok(
            upsert_member(body(req), member_id),
            "Member profile updated."
        )

    except PermissionError as e:
        return fail(
            str(e),
            401 if str(e) == "Login required" else 403,
        )

    except Exception as e:
        return fail(str(e), 400)

@app.route(route="media/upload", methods=["POST"])
def upload(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_login(req)
        data = body(req)
        file_name = clean(data.get("file_name") or "upload.png")
        encoded = clean(data.get("content_base64"))
        if not encoded:
            raise ValueError("content_base64 is required.")
        if "," in encoded:
            encoded = encoded.split(",", 1)[1]
        raw = base64.b64decode(encoded)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file_name)
        blob_name = f"{uuid4()}-{safe_name}"
        service = blob_service()
        try:
            service.create_container(BLOB_IMAGES)
        except ResourceExistsError:
            pass
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        blob = service.get_blob_client(container=BLOB_IMAGES, blob=blob_name)
        blob.upload_blob(raw, overwrite=True, content_settings=ContentSettings(content_type=content_type))
        return ok({"url": blob.url, "blob_name": blob_name}, "Image uploaded.", 201)
    except PermissionError as e:
        return fail(str(e), 401)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="site-image/{file_name}", methods=["GET"])
def site_image(req: func.HttpRequest) -> func.HttpResponse:
    try:
        file_name = re.sub(r"[^A-Za-z0-9_.-]", "_", clean(req.route_params.get("file_name", "")))
        if not file_name:
            return fail("Image name is required.", 400)
        blob = blob_service().get_blob_client(container=BLOB_SITE_IMAGES, blob=file_name)
        raw = blob.download_blob().readall()
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        return func.HttpResponse(raw, status_code=200, mimetype=content_type)
    except ResourceNotFoundError:
        return fail("Site image not found.", 404)
    except Exception as e:
        return fail(str(e), 400)


def admin_summary_response(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN])
        return ok(
            {
                "members": len(list_table_rows(TABLE_MEMBERS)),
                "events": len(list_table_rows(TABLE_EVENTS)),
                "knowledge": len(list_table_rows(TABLE_KNOWLEDGE)),
            },
            "Summary loaded.",
        )
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)


@app.route(route="dashboard/summary", methods=["GET"])
def dashboard_summary(req: func.HttpRequest) -> func.HttpResponse:
    return admin_summary_response(req)



# =========================================================
# Stage 1 legacy API compatibility.
# Remove after /api/members passes browser UAT.
# =========================================================

@app.route(route="alumni", methods=["GET", "POST"])
def legacy_alumni(req: func.HttpRequest) -> func.HttpResponse:
    return members(req)


@app.route(route="alumni/{alumni_id}", methods=["PUT", "DELETE"])
def legacy_alumni_item(req: func.HttpRequest) -> func.HttpResponse:
    legacy_id = clean(req.route_params.get("alumni_id", ""))
    req.route_params["member_id"] = legacy_id
    return member_item(req)

@app.route(route="users", methods=["GET", "POST"])
def users(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_role(req, [ROLE_ADMIN])
        if req.method == "GET":
            return ok([remove_storage_keys(row) for row in list_table_rows(TABLE_USERS)], "Users loaded.")
        data = body(req)
        user = save_user(
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            password=data.get("password", "ChangeMe123!"),
            role=data.get("role", ROLE_READER),
            status=data.get("status", "approved"),
        )
        return ok(remove_storage_keys(user), "User created.", 201)
    except PermissionError as e:
        return fail(str(e), 401 if str(e) == "Login required" else 403)
    except Exception as e:
        return fail(str(e), 400)
