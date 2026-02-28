"""In-memory session store keyed by signed session cookie. No DB, no file storage."""

import hashlib
import hmac
import os
import secrets
from typing import Any

# Session data: { "stripe_access_token": str, "stripe_account_id": str }
_sessions: dict[str, dict[str, Any]] = {}


def _get_secret() -> bytes:
    from core.config import settings
    return settings.SECRET_KEY.encode("utf-8")


def create_session_id() -> str:
    return secrets.token_hex(32)


def sign_session_id(session_id: str) -> str:
    sig = hmac.new(_get_secret(), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{session_id}.{sig}"


def verify_and_get_session_id(cookie_value: str) -> str | None:
    if not cookie_value or "." not in cookie_value:
        return None
    parts = cookie_value.rsplit(".", 1)
    if len(parts) != 2:
        return None
    session_id, sig = parts
    expected = hmac.new(_get_secret(), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return session_id if session_id in _sessions else None


def set_session(session_id: str, data: dict[str, Any]) -> None:
    _sessions[session_id] = data


def get_session(session_id: str) -> dict[str, Any] | None:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def get_creds_from_cookie_value(cookie_value: str | None) -> dict[str, str] | None:
    """Return { stripe_access_token, stripe_account_id } if valid session cookie else None."""
    if not cookie_value:
        return None
    session_id = verify_and_get_session_id(cookie_value)
    if not session_id:
        return None
    data = get_session(session_id)
    if not data:
        return None
    token = data.get("stripe_access_token")
    account_id = data.get("stripe_account_id")
    if token and account_id:
        return {"stripe_access_token": token, "stripe_account_id": account_id}
    return None


COOKIE_NAME = "revenueos_session"
