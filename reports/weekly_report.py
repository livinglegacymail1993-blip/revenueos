"""Pure deterministic weekly operator report. No FastAPI, DB, or network."""

from analysis.bottleneck_detector import detect_primary_constraint
from analysis.experiment_generator import generate_experiments

# Severity from constraint_score (deterministic)
def _severity_level(score: float | None) -> str:
    if score is None:
        return "Low"
    s = float(score)
    if s < 10:
        return "Low"
    if s <= 50:
        return "Moderate"
    if s <= 150:
        return "High"
    return "Critical"


def _confidence_label(confidence: float | None) -> str:
    if confidence is None:
        return "Low"
    c = float(confidence)
    if c < 0.5:
        return "Low"
    if c <= 0.8:
        return "Medium"
    return "High"


# Priority statement one-liner by constraint_type
_PRIORITY_BY_TYPE: dict[str, str] = {
    "revenue_decline": "Stabilize revenue before acquisition or pricing expansion.",
    "churn": "Reduce customer loss before scaling acquisition.",
    "trial_conversion": "Improve conversion efficiency before increasing traffic.",
    "activation": "Increase activation before optimizing pricing.",
}


def _build_operator_summary(
    constraint: dict,
    persistence_weeks: dict[str, int] | None,
    severity_level: str,
    confidence_label: str,
) -> str:
    ctype = (constraint.get("constraint_type") or "constraint").replace("_", " ")
    metric = constraint.get("affected_metric") or "revenue metrics"
    persistence_num: int | None = None
    if persistence_weeks and isinstance(constraint.get("affected_metric"), str):
        persistence_num = persistence_weeks.get(constraint["affected_metric"])
    persist_phrase = f" This trend has persisted for {persistence_num} weeks." if persistence_num is not None else ""
    templates = {
        "revenue_decline": "RevenueOS has identified a revenue decline impacting {metric}. Severity is {severity} with {confidence} confidence."
        + persist_phrase
        + " Delaying action may lead to further revenue erosion. Priority: Stabilize revenue before acquisition or pricing expansion.",
        "churn": "RevenueOS has identified elevated churn impacting {metric}. Severity is {severity} with {confidence} confidence."
        + persist_phrase
        + " Delaying action may compound customer loss. Priority: Reduce customer loss before scaling acquisition.",
        "trial_conversion": "RevenueOS has identified a trial conversion constraint impacting {metric}. Severity is {severity} with {confidence} confidence."
        + persist_phrase
        + " Delaying action may waste acquisition spend. Priority: Improve conversion efficiency before increasing traffic.",
        "activation": "RevenueOS has identified an activation constraint impacting {metric}. Severity is {severity} with {confidence} confidence."
        + persist_phrase
        + " Delaying action may limit revenue per customer. Priority: Increase activation before optimizing pricing.",
    }
    key = constraint.get("constraint_type") or ""
    template = templates.get(
        key,
        f"RevenueOS has identified a constraint ({ctype}) impacting {metric}. Severity is {{severity}} with {{confidence}} confidence. Immediate action recommended.",
    )
    return template.format(
        metric=metric,
        severity=severity_level,
        confidence=confidence_label,
    )


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
    active_experiments, next_action, operator_summary, priority_statement).
    """
    if active_experiments is None:
        active_experiments = []

    constraint = detect_primary_constraint(metrics_7d, metrics_30d, persistence_weeks)

    if constraint is None:
        primary_constraint = None
        recommended_experiments = []
        next_action = "No significant constraint detected. Continue monitoring."
        operator_summary = "No significant constraint detected. Continue monitoring metrics."
        priority_statement = "Immediate Priority: Continue monitoring."
    else:
        primary_constraint = constraint
        recommended_experiments = generate_experiments(constraint, top_n=3)
        if recommended_experiments:
            next_action = f"Run highest-ranked experiment: {recommended_experiments[0].get('title', '')}"
        else:
            next_action = "No significant constraint detected. Continue monitoring."

        score = primary_constraint.get("constraint_score")
        confidence = primary_constraint.get("confidence_score")
        severity_level = _severity_level(score)
        confidence_label = _confidence_label(confidence)
        operator_summary = _build_operator_summary(
            primary_constraint, persistence_weeks, severity_level, confidence_label
        )
        ctype = primary_constraint.get("constraint_type") or ""
        priority_line = _PRIORITY_BY_TYPE.get(ctype, "Address the primary constraint before scaling.")
        priority_statement = f"Immediate Priority: {priority_line}"

    return {
        "current_metrics": metrics_7d,
        "primary_constraint": primary_constraint,
        "recommended_experiments": recommended_experiments,
        "active_experiments": active_experiments,
        "next_action": next_action,
        "operator_summary": operator_summary,
        "priority_statement": priority_statement,
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
