"""Pure deterministic experiment generator. No FastAPI, DB, or external APIs."""

import re


def _parse_impact_midpoint(expected_impact_range: str) -> float:
    """Parse string like '2-5%' or '5–10%' to midpoint percent as float (e.g. 3.5)."""
    s = (expected_impact_range or "").strip()
    parts = re.split(r"[–\-]", s, maxsplit=1)
    if len(parts) != 2:
        return 0.0
    try:
        lo = float(parts[0].strip().rstrip("%"))
        hi = float(parts[1].strip().rstrip("%"))
        return (lo + hi) / 2.0
    except ValueError:
        return 0.0


# At least 3 templates per constraint_type. Each: experiment_id, title, hypothesis,
# implementation_steps, expected_impact_range, effort (1-5), base_confidence (0-1).
TEMPLATES: dict[str, list[dict]] = {
    "churn": [
        {
            "experiment_id": "churn-1-targeted-messaging",
            "title": "Reduce churn with targeted at-risk messaging",
            "hypothesis": "Targeted retention messaging to at-risk customers will reduce churn.",
            "implementation_steps": [
                "Segment customers by usage and payment signals",
                "Define at-risk criteria and messaging",
                "Send targeted emails and in-app messages",
                "Measure churn before/after",
            ],
            "expected_impact_range": "2-5%",
            "effort": 2,
            "base_confidence": 0.7,
        },
        {
            "experiment_id": "churn-2-onboarding-check",
            "title": "Improve onboarding to reduce early churn",
            "hypothesis": "Stronger onboarding reduces first-90-day churn.",
            "implementation_steps": [
                "Audit current onboarding flow",
                "Add key outcome checkpoints",
                "A/B test new flow",
                "Track 90-day retention",
            ],
            "expected_impact_range": "3-7%",
            "effort": 3,
            "base_confidence": 0.6,
        },
        {
            "experiment_id": "churn-3-cancel-flow",
            "title": "Optimize cancel/cancel-flow to save at-risk",
            "hypothesis": "A save flow at cancellation reduces involuntary churn.",
            "implementation_steps": [
                "Add cancel survey and save offers",
                "Train support on save scripts",
                "Track save rate and subsequent retention",
                "Iterate on offers",
            ],
            "expected_impact_range": "1-4%",
            "effort": 2,
            "base_confidence": 0.75,
        },
    ],
    "revenue_decline": [
        {
            "experiment_id": "revenue-decline-1-upsell",
            "title": "Upsell and expansion campaign",
            "hypothesis": "Targeted upsell to existing customers will lift revenue.",
            "implementation_steps": [
                "Identify expansion opportunities by segment",
                "Design upsell offers and cadence",
                "Run campaign and track revenue impact",
                "Scale winning segments",
            ],
            "expected_impact_range": "3-6%",
            "effort": 3,
            "base_confidence": 0.65,
        },
        {
            "experiment_id": "revenue-decline-2-pricing",
            "title": "Pricing and packaging experiment",
            "hypothesis": "Adjusting price or packaging improves revenue without losing volume.",
            "implementation_steps": [
                "Review price elasticity and competitor pricing",
                "Design 1–2 test variants",
                "Run A/B test on new signups",
                "Decide rollout or rollback",
            ],
            "expected_impact_range": "5-10%",
            "effort": 4,
            "base_confidence": 0.5,
        },
        {
            "experiment_id": "revenue-decline-3-reactivation",
            "title": "Reactivate dormant or downgraded users",
            "hypothesis": "Reactivation campaigns recover revenue from lapsed users.",
            "implementation_steps": [
                "Define dormant/downgraded segments",
                "Create reactivation offers and messaging",
                "Execute and measure revenue recovered",
                "Iterate on segments and copy",
            ],
            "expected_impact_range": "2-5%",
            "effort": 2,
            "base_confidence": 0.6,
        },
    ],
    "trial_conversion": [
        {
            "experiment_id": "trial-conversion-1-onboarding",
            "title": "Optimize trial onboarding for conversion",
            "hypothesis": "Clear onboarding increases trial-to-paid conversion.",
            "implementation_steps": [
                "Map current trial journey and drop-off",
                "Add milestones and quick wins",
                "A/B test onboarding changes",
                "Measure conversion and time-to-convert",
            ],
            "expected_impact_range": "4-8%",
            "effort": 3,
            "base_confidence": 0.7,
        },
        {
            "experiment_id": "trial-conversion-2-reminder",
            "title": "Trial reminder and urgency messaging",
            "hypothesis": "Well-timed reminders and soft urgency improve conversion.",
            "implementation_steps": [
                "Set reminder schedule (mid-trial, near expiry)",
                "Draft emails and in-app copy",
                "Run experiment vs no-reminder",
                "Measure conversion lift",
            ],
            "expected_impact_range": "2-5%",
            "effort": 1,
            "base_confidence": 0.75,
        },
        {
            "experiment_id": "trial-conversion-3-paywall",
            "title": "Paywall and CTA placement",
            "hypothesis": "Clear paywall and CTA placement increase conversion.",
            "implementation_steps": [
                "Audit paywall and CTA placement",
                "Test 1–2 variants (copy and placement)",
                "Measure conversion and trial satisfaction",
                "Roll out winner",
            ],
            "expected_impact_range": "3-6%",
            "effort": 2,
            "base_confidence": 0.65,
        },
    ],
    "activation": [
        {
            "experiment_id": "activation-1-guided-setup",
            "title": "Guided setup and first-value path",
            "hypothesis": "Guided setup increases time-to-first-value and activation.",
            "implementation_steps": [
                "Define activation outcome and steps",
                "Build guided flow (checklist or wizard)",
                "A/B test vs unguided",
                "Measure activation rate and retention",
            ],
            "expected_impact_range": "5-10%",
            "effort": 3,
            "base_confidence": 0.65,
        },
        {
            "experiment_id": "activation-2-email-sequence",
            "title": "Activation email sequence",
            "hypothesis": "Email sequence nudges users to key actions and activation.",
            "implementation_steps": [
                "Define key actions and sequence timing",
                "Write and schedule emails",
                "Run test vs no sequence",
                "Measure activation and engagement",
            ],
            "expected_impact_range": "2-5%",
            "effort": 2,
            "base_confidence": 0.7,
        },
        {
            "experiment_id": "activation-3-tooltips",
            "title": "In-app tooltips and empty states",
            "hypothesis": "Tooltips and empty states improve feature discovery and activation.",
            "implementation_steps": [
                "Audit underused features and empty states",
                "Add tooltips and clear next steps",
                "Measure feature use and activation",
                "Iterate on copy and placement",
            ],
            "expected_impact_range": "3-6%",
            "effort": 2,
            "base_confidence": 0.6,
        },
    ],
}

# Generic fallback when constraint_type is unknown (exactly 3 experiments).
GENERIC_TEMPLATES: list[dict] = [
    {
        "experiment_id": "generic-1-review-metrics",
        "title": "Review key metrics and hypotheses",
        "hypothesis": "Structured review of metrics will surface the next best experiment.",
        "implementation_steps": [
            "Gather current metrics and trends",
            "List top hypotheses by impact and ease",
            "Pick one to test and define success",
            "Run and measure",
        ],
        "expected_impact_range": "1-4%",
        "effort": 2,
        "base_confidence": 0.5,
    },
    {
        "experiment_id": "generic-2-customer-feedback",
        "title": "Customer feedback and interviews",
        "hypothesis": "Direct feedback will reveal high-impact improvements.",
        "implementation_steps": [
            "Select segment and recruit users",
            "Run interviews or surveys",
            "Synthesize themes and ideas",
            "Prioritize one experiment",
        ],
        "expected_impact_range": "2-5%",
        "effort": 3,
        "base_confidence": 0.55,
    },
    {
        "experiment_id": "generic-3-small-test",
        "title": "Run a small, fast experiment",
        "hypothesis": "A small test will reduce uncertainty on a key lever.",
        "implementation_steps": [
            "Choose one lever and metric",
            "Design minimal test",
            "Execute and analyze",
            "Decide scale or pivot",
        ],
        "expected_impact_range": "1-3%",
        "effort": 1,
        "base_confidence": 0.6,
    },
]


def generate_experiments(primary_constraint: dict, top_n: int = 3) -> list[dict]:
    """
    Return exactly top_n experiments (default 3) for the given primary_constraint.
    Reads constraint_type and confidence_score from primary_constraint.
    Deterministic: same inputs -> same outputs.
    """
    constraint_type = primary_constraint.get("constraint_type") or "unknown"
    constraint_conf = primary_constraint.get("confidence_score", 0.5)
    constraint_conf = max(0.0, min(1.0, float(constraint_conf)))

    if constraint_type in TEMPLATES:
        template_list = TEMPLATES[constraint_type]
    else:
        template_list = GENERIC_TEMPLATES

    experiments: list[dict] = []
    for t in template_list:
        base_conf = max(0.0, min(1.0, float(t.get("base_confidence", 0.5))))
        confidence_score = base_conf * constraint_conf
        confidence_score = max(0.0, min(1.0, confidence_score))

        impact_midpoint = _parse_impact_midpoint(t.get("expected_impact_range") or "0-0%")
        effort = max(1, min(5, int(t.get("effort", 3))))
        score = (impact_midpoint * confidence_score) / effort if effort else 0.0

        experiments.append({
            "experiment_id": t["experiment_id"],
            "title": t["title"],
            "hypothesis": t["hypothesis"],
            "implementation_steps": list(t["implementation_steps"]),
            "expected_impact_range": t["expected_impact_range"],
            "effort": effort,
            "base_confidence": base_conf,
            "confidence_score": confidence_score,
            "score": score,
        })

    experiments.sort(key=lambda x: x["score"], reverse=True)
    return experiments[:top_n]
