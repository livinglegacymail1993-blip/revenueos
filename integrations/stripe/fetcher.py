"""Pure Stripe subscription fetcher. No FastAPI, no DB. Uses official Stripe SDK."""

from datetime import datetime, timezone
from typing import Any

import stripe

# Subscription statuses to include (at minimum).
_INCLUDED_STATUSES = ("active", "trialing", "past_due")

# Allowed billing intervals (Stripe uses month/year/week/day).
_VALID_INTERVALS = frozenset({"month", "year", "week", "day"})


def _unix_to_iso_date(ts: int | None) -> str:
    """
    Convert a Unix timestamp to ISO date string 'YYYY-MM-DD' in UTC.
    Returns empty string if ts is None or invalid.
    """
    if ts is None:
        return ""
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, OSError, TypeError):
        return ""


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute or dict key from Stripe object or dict."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _subscription_to_record(sub: Any) -> dict | None:
    """
    Convert a Stripe Subscription to a SubscriptionRecord-shaped dict.
    Returns None if the subscription has no first item, no price, or missing unit_amount.
    """
    items = _get(sub, "items")
    if not items:
        return None
    data = _get(items, "data")
    if not data:
        return None
    first_item = data[0]
    price = _get(first_item, "price")
    if not price:
        return None

    unit_amount = _get(price, "unit_amount")
    if unit_amount is None:
        return None
    try:
        amount = float(unit_amount) / 100.0
    except (TypeError, ValueError):
        return None

    recurring = _get(price, "recurring") or {}
    raw_interval = (_get(recurring, "interval") or "month")
    interval = str(raw_interval).strip().lower() if raw_interval else "month"
    if interval not in _VALID_INTERVALS:
        interval = "month"

    created = _get(sub, "created")
    start_date = _unix_to_iso_date(created) if created is not None else ""
    if not start_date:
        return None

    ended_at = _get(sub, "ended_at")
    cancel_at = _get(sub, "cancel_at")
    end_ts = ended_at if ended_at is not None else cancel_at
    end_date = _unix_to_iso_date(end_ts) if end_ts is not None else ""

    return {
        "start_date": start_date,
        "end_date": end_date,
        "amount": amount,
        "billing_interval": interval,
    }


def fetch_subscriptions(stripe_api_key: str) -> list[dict]:
    """
    Fetch subscriptions from Stripe and return them as SubscriptionRecord-shaped dicts.

    Uses the official Stripe SDK with auto-pagination so all matching subscriptions
    are returned (not limited to 100). Includes subscriptions with status in
    ("active", "trialing", "past_due"). Each record has:
    - start_date: ISO "YYYY-MM-DD"
    - end_date: ISO "YYYY-MM-DD" or "" for no end
    - amount: float (first item price unit_amount / 100.0); subscriptions without
      unit_amount are skipped
    - billing_interval: "month" | "year" | "week" | "day"

    Deterministic: no randomness, no printing, no global state beyond stripe.api_key.
    """
    stripe.api_key = stripe_api_key
    result: list[dict] = []
    for status in _INCLUDED_STATUSES:
        for sub in stripe.Subscription.list(status=status, limit=100).auto_paging_iter():
            rec = _subscription_to_record(sub)
            if rec is not None:
                result.append(rec)
    return result
