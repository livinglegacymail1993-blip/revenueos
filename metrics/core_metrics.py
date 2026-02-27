"""Pure, deterministic SaaS metric calculations. No FastAPI, DB, or external APIs."""

from datetime import date, datetime
from typing import NotRequired, TypedDict

# Normalization factors: subscription amount per interval -> monthly equivalent
_MONTHLY_FACTOR = {
    "month": 1.0,
    "year": 1.0 / 12,
    "week": 4.345,
    "day": 30.437,
}


class SubscriptionRecord(TypedDict):
    """Minimal record for subscription-based metrics."""

    start_date: str  # ISO "YYYY-MM-DD"
    end_date: NotRequired[str]  # Optional. ISO "YYYY-MM-DD"; missing/""/None = active indefinitely
    amount: float  # Amount per billing_interval
    billing_interval: str  # One of: "month", "year", "week", "day"


def _parse_date(s: str | None) -> date | None:
    """Parse ISO date 'YYYY-MM-DD'. Returns None for empty/None."""
    if not s or not str(s).strip():
        return None
    return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()


def _normalize_to_monthly(amount: float, billing_interval: str) -> float:
    """Normalize subscription amount to monthly value. Raises ValueError for unknown interval."""
    bi = (billing_interval or "").strip().lower()
    if bi not in _MONTHLY_FACTOR:
        raise ValueError(f"billing_interval must be one of {list(_MONTHLY_FACTOR.keys())!r}, got {billing_interval!r}")
    return amount * _MONTHLY_FACTOR[bi]


def _active_at(sub: SubscriptionRecord, d: date) -> bool:
    """True if subscription is active on date d (start_date <= d and no end or end_date >= d)."""
    start = _parse_date(sub.get("start_date"))
    end = _parse_date(sub.get("end_date"))  # None for missing or ""
    if start is None:
        return False
    if start > d:
        return False
    if end is None:
        return True
    return end >= d


def calculate_mrr(
    subscriptions: list[SubscriptionRecord],
    as_of: str | None = None,
) -> float:
    """
    Sum of monthly-normalized revenue for subscriptions active at as_of (default: today).
    Returns MRR as a non-negative float.
    """
    if not subscriptions:
        return 0.0
    ref = _parse_date(as_of) if as_of else date.today()
    if ref is None:
        ref = date.today()
    total = 0.0
    for sub in subscriptions:
        if not _active_at(sub, ref):
            continue
        amount = float(sub.get("amount", 0) or 0)
        total += _normalize_to_monthly(amount, sub.get("billing_interval") or "month")
    return total


def calculate_churn_rate(
    subscriptions: list[SubscriptionRecord],
    period_start: str,
    period_end: str,
) -> float:
    """
    Customer churn rate over the period: (active at start - active at end) / active at start.
    Returns a ratio in [0.0, 1.0]. Returns 0.0 if invalid range (period_end < period_start),
    no customers at period start, or unparseable dates.
    """
    start = _parse_date(period_start)
    end = _parse_date(period_end)
    if start is None or end is None:
        return 0.0
    if end < start:
        return 0.0
    active_start = sum(1 for sub in subscriptions if _active_at(sub, start))
    active_end = sum(1 for sub in subscriptions if _active_at(sub, end))
    if active_start == 0:
        return 0.0
    churned = max(0, active_start - active_end)
    churn_rate = churned / active_start
    return max(0.0, min(1.0, churn_rate))


def calculate_active_customers(
    subscriptions: list[SubscriptionRecord],
    as_of: str | None = None,
) -> int:
    """
    Count subscriptions active at as_of (default: today).
    Uses the same _active_at logic as calculate_mrr.
    """
    if not subscriptions:
        return 0
    ref = _parse_date(as_of) if as_of else date.today()
    if ref is None:
        ref = date.today()
    return sum(1 for sub in subscriptions if _active_at(sub, ref))


def calculate_arpu(mrr: float, active_customers: int) -> float:
    """
    Average Revenue Per User: MRR / active_customers.
    Returns 0.0 when active_customers is 0.
    """
    if active_customers <= 0:
        return 0.0
    return mrr / active_customers


def calculate_revenue_velocity(mrr_previous: float, mrr_current: float) -> float:
    """
    Period-over-period change in MRR: (mrr_current - mrr_previous) / mrr_previous.
    Can be negative. Returns 0.0 when mrr_previous is 0.
    """
    if mrr_previous == 0:
        return 0.0
    return (mrr_current - mrr_previous) / mrr_previous


def calculate_net_revenue_growth(mrr_start: float, mrr_end: float) -> float:
    """
    Net revenue growth ratio: (mrr_end - mrr_start) / mrr_start.
    Returns a ratio (e.g. 0.1 = 10% growth). Returns 0.0 when mrr_start is 0.
    """
    if mrr_start == 0:
        return 0.0
    return (mrr_end - mrr_start) / mrr_start
