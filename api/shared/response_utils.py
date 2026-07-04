from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_response(
    message: str = "Success",
    data: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> Dict:
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": [],
        "timestamp": utc_now(),
        "request_id": request_id or str(uuid4()),
    }


def error_response(
    message: str = "Error",
    errors: Optional[List[str]] = None,
    data: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> Dict:
    return {
        "success": False,
        "message": message,
        "data": data,
        "errors": errors or [],
        "timestamp": utc_now(),
        "request_id": request_id or str(uuid4()),
    }


def validation_error(
    message: str = "Validation failed",
    errors: Optional[List[str]] = None,
) -> Dict:
    return error_response(
        message=message,
        errors=errors or [],
    )


def unauthorized_response(
    message: str = "Unauthorized",
) -> Dict:
    return error_response(
        message=message,
        errors=["Authentication required."],
    )


def forbidden_response(
    message: str = "Forbidden",
) -> Dict:
    return error_response(
        message=message,
        errors=["You do not have permission to perform this action."],
    )