# Worse direction: higher is worse for churn; lower is worse for revenue/growth/rates
_HIGHER_WORSE: set[str] = {"churn_rate"}
_LOWER_WORSE: set[str] = {"mrr", "net_revenue_growth", "arpu", "trial_conversion_rate", "activation_rate", "revenue_velocity"}

_REVENUE_DECLINE_CANDIDATES: list[str] = ["net_revenue_growth", "revenue_velocity", "mrr"]
_SCORE_EPSILON = 1e-9
_DELTA_PCT_CLAMP = (-200.0, 200.0)
_SMALL_BASELINE_THRESHOLD = 0.02


def detect_primary_constraint(
    metrics_7d: dict[str, float],
    metrics_30d: dict[str, float],
    persistence_weeks: dict[str, int] | None = None,
) -> dict | None:
    """
    Detect the primary revenue constraint from 7-day vs 30-day metrics.

    Uses negative revenue-impact direction per metric, constraint_score and
    confidence_score formulas, and min_severity threshold. Returns None if
    no constraint exceeds the threshold. Tie-break: higher impact weight wins.
    """
    if persistence_weeks is None:
        persistence_weeks = {}

    constraints: list[tuple[str, float, str]] = [
        ("churn", 1.3, "churn_rate"),
        ("trial_conversion", 1.0, "trial_conversion_rate"),
        ("activation", 0.9, "activation_rate"),
    ]
    # revenue_decline: first candidate metric present in inputs
    rev_metric = None
    for m in _REVENUE_DECLINE_CANDIDATES:
        if m in metrics_7d and m in metrics_30d:
            rev_metric = m
            break
    if rev_metric is not None:
        constraints.append(("revenue_decline", 1.1, rev_metric))

    min_severity = 3.0
    threshold_pct = 5.0
    best_constraint: dict | None = None
    best_weight = 0.0

    for constraint_type, impact_weight, affected_metric in constraints:
        current = metrics_7d.get(affected_metric)
        baseline = metrics_30d.get(affected_metric)

        if baseline is None or current is None:
            continue
        if baseline == 0:
            continue  # avoid division by zero

        deviation_percentage = ((current - baseline) / baseline) * 100
        delta_percentage_clamped = max(_DELTA_PCT_CLAMP[0], min(_DELTA_PCT_CLAMP[1], deviation_percentage))

        # Per-metric worse direction
        if affected_metric in _HIGHER_WORSE:
            if current <= baseline:
                continue  # churn: worse only when current > baseline
        elif affected_metric in _LOWER_WORSE:
            if current >= baseline:
                continue  # revenue/growth/rates: worse only when current < baseline
        else:
            continue  # unknown metric, skip

        weeks = persistence_weeks.get(affected_metric, 1)
        if weeks >= 3:
            persistence_factor = 1.5
        elif weeks == 2:
            persistence_factor = 1.2
        else:
            persistence_factor = 1.0

        constraint_score = abs(deviation_percentage) * impact_weight * persistence_factor
        confidence_score = min(
            1.0,
            (abs(deviation_percentage) / threshold_pct) * (persistence_factor / 1.5),
        )

        if constraint_score < min_severity:
            continue

        explanation = f"Deviation of {delta_percentage_clamped:.2f}% for {affected_metric} leads to a score of {constraint_score:.2f}"
        if abs(baseline) < _SMALL_BASELINE_THRESHOLD:
            explanation += " (baseline small; percentage swings exaggerated)"

        # Tie-break: equal score within epsilon -> higher impact weight wins
        if best_constraint is None:
            best_constraint = {
                "constraint_type": constraint_type,
                "affected_metric": affected_metric,
                "delta_percentage": delta_percentage_clamped,
                "constraint_score": constraint_score,
                "confidence_score": confidence_score,
                "explanation": explanation,
            }
            best_weight = impact_weight
            continue

        best_score = best_constraint["constraint_score"]
        if constraint_score > best_score:
            best_constraint = {
                "constraint_type": constraint_type,
                "affected_metric": affected_metric,
                "delta_percentage": delta_percentage_clamped,
                "constraint_score": constraint_score,
                "confidence_score": confidence_score,
                "explanation": explanation,
            }
            best_weight = impact_weight
        elif abs(constraint_score - best_score) < _SCORE_EPSILON and impact_weight > best_weight:
            best_constraint = {
                "constraint_type": constraint_type,
                "affected_metric": affected_metric,
                "delta_percentage": delta_percentage_clamped,
                "constraint_score": constraint_score,
                "confidence_score": confidence_score,
                "explanation": explanation,
            }
            best_weight = impact_weight

    return best_constraint