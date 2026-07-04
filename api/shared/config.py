"""
==========================================================
NUST KSA Alumni Portal
Application Configuration

Author : Hashim Hilal
==========================================================
"""

from pathlib import Path
import os
import json


# ==========================================================
# Application
# ==========================================================

APPLICATION_NAME = "NUST KSA Alumni Portal"

APPLICATION_VERSION = "1.0.0"

UNIVERSITY_ID = "NUST-KSA"

DEFAULT_TIMEZONE = "Asia/Riyadh"

# ==========================================================
# Environment Variables
# ==========================================================

ENV_STORAGE_CONNECTION = "AZURE_STORAGE_CONNECTION_STRING"

ENV_STORAGE_CONNECTION_STRING = "AZURE_STORAGE_CONNECTION_STRING"

ENV_JWT_SECRET = "JWT_SECRET"

ENV_APPLICATION_NAME = "APPLICATION_NAME"


# ==========================================================
# Azure Storage
# ==========================================================

TABLES = {

    "users": "UserAccounts",

    "alumni": "AlumniProfiles",

    "registration_requests": "RegistrationRequests",

    "sessions": "Sessions",

    "login_tokens": "LoginTokens",

    "events": "Events",

    "event_registrations": "EventRegistrations",

    "blogs": "BlogPosts",

    "media": "MediaAssets",

    "audit": "AuditLogs",

    "imports": "ImportJobs",

    "settings": "SystemSettings",
}


BLOB_CONTAINERS = {

    "profile_images": "profile-images",

    "blog_images": "blog-images",

    "event_images": "event-images",

    "blog_content": "blog-content",

    "event_assets": "event-assets",

    "documents": "documents",

    "imports": "imports",
}


# ==========================================================
# Authentication
# ==========================================================

SESSION_TIMEOUT_HOURS = 8

PASSWORD_RESET_TOKEN_HOURS = 1

LOGIN_TOKEN_MINUTES = 10

MAX_LOGIN_ATTEMPTS = 5

# ==========================================================
# Password Policy
# ==========================================================

PASSWORD_POLICY = {
    "min_length": 10,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_symbol": True,
    "bcrypt_rounds": 12,
}

# ==========================================================
# Media Upload Limits
# ==========================================================

MAX_PROFILE_IMAGE_MB = 5

MAX_EVENT_IMAGE_MB = 10

MAX_BLOG_IMAGE_MB = 10

MAX_DOCUMENT_MB = 25


ALLOWED_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp"
]


ALLOWED_DOCUMENT_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".csv"
]


# ==========================================================
# Alumni Search
# ==========================================================

DEFAULT_PAGE_SIZE = 25

MAX_PAGE_SIZE = 100

DEFAULT_SORT = "full_name"


# ==========================================================
# Roles
# ==========================================================

ROLE_ADMIN = "admin"

ROLE_CONTRIBUTOR = "contributor"

ROLE_ALUMNI = "alumni"


ROLES = [
    ROLE_ADMIN,
    ROLE_CONTRIBUTOR,
    ROLE_ALUMNI,
]


# ==========================================================
# Account Status
# ==========================================================

STATUS_PENDING = "pending"

STATUS_APPROVED = "approved"

STATUS_REJECTED = "rejected"

STATUS_SUSPENDED = "suspended"

STATUS_ACTIVE = "active"

STATUS_INACTIVE = "inactive"


# ==========================================================
# Blog Status
# ==========================================================

BLOG_DRAFT = "draft"

BLOG_SUBMITTED = "submitted"

BLOG_APPROVED = "approved"

BLOG_PUBLISHED = "published"

BLOG_REJECTED = "rejected"


# ==========================================================
# Event Status
# ==========================================================

EVENT_DRAFT = "draft"

EVENT_PUBLISHED = "published"

EVENT_CANCELLED = "cancelled"

EVENT_COMPLETED = "completed"




# ==========================================================
# Project Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

API_ROOT = Path(__file__).resolve().parents[1]

FRONTEND_ROOT = PROJECT_ROOT / "frontend"

DOCS_ROOT = PROJECT_ROOT / "docs"

SCRIPTS_ROOT = PROJECT_ROOT / "scripts"


# ==========================================================
# Helper Functions
# ==========================================================

def get_table(name: str) -> str:
    return TABLES[name]


def get_container(name: str) -> str:
    return BLOB_CONTAINERS[name]


def get_env(key: str, default=None):
    value = os.environ.get(key)
    if value:
        return value

    settings_path = API_ROOT / "local.settings.json"

    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            value = settings.get("Values", {}).get(key)
            if value:
                return value
        except Exception:
            pass

    return default