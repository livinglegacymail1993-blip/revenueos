"""Stripe Connect OAuth and session management. No DB; in-memory session store."""

import urllib.parse
import urllib.request

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from core.config import settings
from core.session_store import (
    COOKIE_NAME,
    create_session_id,
    delete_session,
    get_session,
    set_session,
    sign_session_id,
    verify_and_get_session_id,
)

connect_router = APIRouter(prefix="/connect", tags=["connect"])
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _redirect_uri(request: Request) -> str:
    if settings.STRIPE_REDIRECT_URI:
        return settings.STRIPE_REDIRECT_URI.rstrip("/")
    base = str(request.base_url).rstrip("/")
    return f"{base}/connect/stripe/callback"


def _get_session_id_from_cookie(request: Request) -> str | None:
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    return verify_and_get_session_id(cookie)


@connect_router.get("/stripe")
def connect_stripe_start(request: Request):
    """Redirect user to Stripe OAuth authorize URL."""
    if not settings.STRIPE_CLIENT_ID:
        return RedirectResponse(url="/console?error=stripe_not_configured", status_code=302)
    redirect_uri = _redirect_uri(request)
    params = {
        "response_type": "code",
        "client_id": settings.STRIPE_CLIENT_ID,
        "scope": "read_only",
        "redirect_uri": redirect_uri,
    }
    url = "https://connect.stripe.com/oauth/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=url, status_code=302)


@connect_router.get("/stripe/callback")
def connect_stripe_callback(request: Request, code: str | None = None, error: str | None = None):
    """Exchange code for access token, store in session, redirect to /console."""
    if error or not code:
        return RedirectResponse(url="/console?error=oauth_denied", status_code=302)
    if not settings.STRIPE_CLIENT_SECRET:
        return RedirectResponse(url="/console?error=stripe_not_configured", status_code=302)

    redirect_uri = _redirect_uri(request)
    body = urllib.parse.urlencode({
        "client_id": settings.STRIPE_CLIENT_ID,
        "client_secret": settings.STRIPE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://connect.stripe.com/oauth/token",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
            import json
            payload = json.loads(data)
    except Exception:
        return RedirectResponse(url="/console?error=token_exchange_failed", status_code=302)

    access_token = payload.get("access_token")
    stripe_user_id = payload.get("stripe_user_id")
    if not access_token or not stripe_user_id:
        return RedirectResponse(url="/console?error=token_exchange_failed", status_code=302)

    session_id = create_session_id()
    set_session(session_id, {
        "stripe_access_token": access_token,
        "stripe_account_id": stripe_user_id,
    })
    signed = sign_session_id(session_id)
    response = RedirectResponse(url="/console", status_code=302)
    response.set_cookie(
        key=COOKIE_NAME,
        value=signed,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


@connect_router.get("/status")
def connect_status(request: Request):
    """Return { connected: bool, account_id?: str, stripe_configured: bool }."""
    stripe_configured = bool(settings.STRIPE_CLIENT_ID and settings.STRIPE_CLIENT_SECRET)
    session_id = _get_session_id_from_cookie(request)
    if not session_id:
        return {"connected": False, "stripe_configured": stripe_configured}
    data = get_session(session_id)
    if not data:
        return {"connected": False, "stripe_configured": stripe_configured}
    return {
        "connected": True,
        "account_id": data.get("stripe_account_id"),
        "stripe_configured": stripe_configured,
    }


@connect_router.post("/logout")
def connect_logout(request: Request):
    """Clear session and cookie; redirect to console."""
    session_id = _get_session_id_from_cookie(request)
    if session_id:
        delete_session(session_id)
    res = RedirectResponse(url="/console", status_code=302)
    res.delete_cookie(COOKIE_NAME)
    return res
