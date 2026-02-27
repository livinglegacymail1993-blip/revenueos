"""Analyze router: bottleneck detection and experiment recommendations."""

from datetime import date, timedelta

import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from integrations.stripe.fetcher import fetch_subscriptions
from metrics.core_metrics import (
    calculate_active_customers,
    calculate_arpu,
    calculate_churn_rate,
    calculate_mrr,
    calculate_net_revenue_growth,
)
from reports.weekly_report import format_weekly_report, generate_weekly_report

analyze_router = APIRouter(prefix="/analyze", tags=["analyze"])


@analyze_router.get("")
def analyze_root():
    """Placeholder for analyze endpoints."""
    return {"analyze": "ok"}


class StripeAnalyzeBody(BaseModel):
    stripe_api_key: str
    debug: bool = False


@analyze_router.post("/stripe")
def analyze_stripe(body: StripeAnalyzeBody):
    """
    Run Stripe-connected analysis: fetch subscriptions, compute metrics, and return
    a weekly operator report (raw dict + formatted string).
    Body: { "stripe_api_key": "sk_test_..." }
    """
    stripe_api_key = (body.stripe_api_key or "").strip()
    if not stripe_api_key:
        raise HTTPException(status_code=400, detail="stripe_api_key is required")

    today = date.today()
    period_end = today.isoformat()
    period_start_7d = (today - timedelta(days=7)).isoformat()
    period_start_30d = (today - timedelta(days=30)).isoformat()

    try:
        subs = fetch_subscriptions(stripe_api_key)
    except stripe.error.AuthenticationError:
        raise HTTPException(status_code=401, detail="Stripe authentication failed")
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    mrr_now = calculate_mrr(subs, as_of=period_end)
    mrr_30d = calculate_mrr(subs, as_of=period_start_30d)
    churn_7d = calculate_churn_rate(subs, period_start_7d, period_end)
    churn_30d = calculate_churn_rate(subs, period_start_30d, period_end)
    active_now = calculate_active_customers(subs, as_of=period_end)
    arpu_now = calculate_arpu(mrr_now, active_now)
    net_growth = calculate_net_revenue_growth(mrr_30d, mrr_now)

    metrics_7d = {
        "mrr": mrr_now,
        "churn_rate": churn_7d,
        "net_revenue_growth": net_growth,
        "arpu": arpu_now,
    }
    metrics_30d = {
        "mrr": mrr_30d,
        "churn_rate": churn_30d,
        "net_revenue_growth": 0.0,
        "arpu": arpu_now,
    }

    report = generate_weekly_report(
        metrics_7d, metrics_30d, persistence_weeks=None, active_experiments=[]
    )
    formatted = format_weekly_report(report)

    if body.debug:
        return {
            "subscription_count": len(subs),
            "sample_subscription": subs[0] if subs else None,
            "report": report,
            "formatted": formatted,
        }
    return {"report": report, "formatted": formatted}


@analyze_router.post("/demo")
def analyze_demo():
    """Demo analysis with hardcoded SaaS metrics. No Stripe calls."""
    metrics_7d = {
        "mrr": 42000,
        "churn_rate": 0.06,
        "net_revenue_growth": -0.02,
        "arpu": 70,
    }
    metrics_30d = {
        "mrr": 45000,
        "churn_rate": 0.03,
        "net_revenue_growth": 0.01,
        "arpu": 75,
    }
    persistence_weeks = {
        "churn_rate": 2,
        "net_revenue_growth": 2,
    }
    active_experiments = []
    report = generate_weekly_report(
        metrics_7d, metrics_30d, persistence_weeks=persistence_weeks, active_experiments=active_experiments
    )
    formatted = format_weekly_report(report)
    return {"report": report, "formatted": formatted}
