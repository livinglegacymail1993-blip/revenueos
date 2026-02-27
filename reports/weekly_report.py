"""Pure deterministic weekly operator report. No FastAPI, DB, or network."""

from analysis.bottleneck_detector import detect_primary_constraint
from analysis.experiment_generator import generate_experiments


def generate_weekly_report(
    metrics_7d: dict[str, float],
    metrics_30d: dict[str, float],
    persistence_weeks: dict[str, int] | None = None,
    active_experiments: list[dict] | None = None,
) -> dict:
    """
    Build the weekly operator report dict from 7d/30d metrics and optional persistence/experiments.

    Uses detect_primary_constraint and generate_experiments. Returns the exact structure
    expected by MVP_SPEC (current_metrics, primary_constraint, recommended_experiments,
    active_experiments, next_action).
    """
    if active_experiments is None:
        active_experiments = []

    constraint = detect_primary_constraint(metrics_7d, metrics_30d, persistence_weeks)

    if constraint is None:
        primary_constraint = None
        recommended_experiments = []
        next_action = "No significant constraint detected. Continue monitoring."
    else:
        primary_constraint = constraint
        recommended_experiments = generate_experiments(constraint, top_n=3)
        if recommended_experiments:
            next_action = f"Run highest-ranked experiment: {recommended_experiments[0].get('title', '')}"
        else:
            next_action = "No significant constraint detected. Continue monitoring."

    return {
        "current_metrics": metrics_7d,
        "primary_constraint": primary_constraint,
        "recommended_experiments": recommended_experiments,
        "active_experiments": active_experiments,
        "next_action": next_action,
    }


def _fmt_currency(v: float | None) -> str:
    """Format number as currency with commas (e.g. $42,000). Returns N/A if v is None or not float. Deterministic."""
    if v is None:
        return "N/A"
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_pct(v: float | None) -> str:
    """Format ratio as percentage with 1 decimal (e.g. 6.0%). Returns N/A if v is None or not float. Deterministic."""
    if v is None:
        return "N/A"
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_weekly_report(report: dict) -> str:
    """
    Produce a readable multi-line string from a weekly report dict.
    Includes current metrics (MRR, churn_rate, net_revenue_growth, arpu if present),
    primary constraint summary, top recommended experiment, and next action.
    Deterministic.
    """
    lines: list[str] = [
        "=== RevenueOS Weekly Operator Report ===",
        "",
    ]

    metrics = report.get("current_metrics") or {}
    lines.append("Current Metrics:")
    if "mrr" in metrics:
        lines.append(f"  MRR: {_fmt_currency(metrics['mrr'])}")
    if "churn_rate" in metrics:
        lines.append(f"  Churn rate: {_fmt_pct(metrics['churn_rate'])}")
    if "net_revenue_growth" in metrics:
        lines.append(f"  Net revenue growth: {_fmt_pct(metrics['net_revenue_growth'])}")
    if "arpu" in metrics:
        lines.append(f"  ARPU: {_fmt_currency(metrics['arpu'])}")
    if not any(k in metrics for k in ("mrr", "churn_rate", "net_revenue_growth", "arpu")):
        lines.append("  (none)")

    primary = report.get("primary_constraint")
    lines.append("")
    lines.append("Primary Constraint:")
    if primary:
        delta = primary.get("delta_percentage")
        delta_str = f"{float(delta):.1f}%" if delta is not None else "N/A"
        score = primary.get("constraint_score")
        score_str = f"{float(score):.2f}" if score is not None else "N/A"
        conf = primary.get("confidence_score")
        conf_str = f"{float(conf):.2f}" if conf is not None else "N/A"
        lines.append(f"  Type: {primary.get('constraint_type', 'N/A')}")
        lines.append(f"  Metric: {primary.get('affected_metric', 'N/A')}")
        lines.append(f"  Delta: {delta_str}")
        lines.append(f"  Score: {score_str}")
        lines.append(f"  Confidence: {conf_str}")
    else:
        lines.append("  None")

    recs = report.get("recommended_experiments") or []
    lines.append("")
    lines.append("Top Recommended Experiment:")
    if recs:
        top = recs[0]
        lines.append(f"  {top.get('title', '')}")
        lines.append(f"  Expected impact: {top.get('expected_impact_range', 'N/A')}")
        lines.append(f"  Effort: {top.get('effort', 'N/A')}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Next Action:")
    lines.append(f"  {report.get('next_action', '')}")

    return "\n".join(lines)
