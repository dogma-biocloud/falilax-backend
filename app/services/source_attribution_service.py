from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.alert import Alert


def _safe_probability(value: int) -> int:
    return max(0, min(100, value))


def _candidate(
    *,
    source_type: str,
    label: str,
    probability: int,
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "source_type": source_type,
        "label": label,
        "probability": _safe_probability(probability),
        "evidence": evidence,
    }


def get_source_attribution(db: Session, site_id: int) -> dict[str, Any]:
    """
    First-pass source attribution model.

    Strategy:
    - Look at the most recent alert for the requested site/scope_id
    - Use source attribution hints + water quality context
    - Return a frontend-friendly structured explanation
    """
    alert = db.execute(
        select(Alert)
        .where(Alert.scope_id == site_id)
        .order_by(desc(Alert.last_seen_at), desc(Alert.id))
        .limit(1)
    ).scalars().first()

    if not alert:
        return {
            "assessment_type": "inferred",
            "headline": "No attribution data available yet",
            "summary": "No recent signals were found for this site.",
            "confidence_score": 0,
            "confidence_label": "insufficient data",
            "candidates": [],
            "immediate_actions": ["Collect additional water samples for this site."],
            "follow_up_actions": ["Re-run attribution after new measurements are ingested."],
            "explanation": "Attribution could not be generated because no recent alerts or signal patterns were found.",
            "data_sources": [
                "FalilaX alert history",
                "FalilaX measurement history",
            ],
        }

    tier = (getattr(alert, "tier", "NOTICE") or "NOTICE").upper()
    origin_scope_type = (getattr(alert, "origin_scope_type", "unknown") or "unknown").lower()
    parameter_code = (getattr(alert, "parameter_code", "unknown") or "unknown").lower()
    measured_value = getattr(alert, "measured_value", None)
    threshold = getattr(alert, "threshold", None)
    location_label = getattr(alert, "location_label", None)

    candidates: list[dict[str, Any]] = []

    # Default evidence bucket
    common_evidence: list[str] = []
    if location_label:
        common_evidence.append(f"Most recent flagged site: {location_label}.")
    if measured_value is not None and threshold is not None:
        common_evidence.append(
            f"Measured value {measured_value} exceeded reference threshold {threshold}."
        )
    elif measured_value is not None:
        common_evidence.append(f"Measured value recorded at {measured_value}.")

    # Rule-driven inference
    if origin_scope_type == "site":
        candidates = [
            _candidate(
                source_type="building_plumbing",
                label="Building Plumbing",
                probability=68 if tier == "ACTION" else 78 if tier == "CRITICAL" else 55,
                evidence=common_evidence + [
                    "Source attribution from upstream system suggests a local site-level issue.",
                    "Signal concentration is consistent with infrastructure inside the building or facility.",
                ],
            ),
            _candidate(
                source_type="distribution_system",
                label="Distribution System",
                probability=22,
                evidence=[
                    "Distribution contribution cannot be ruled out completely.",
                    "Upstream infrastructure may still influence downstream readings.",
                ],
            ),
            _candidate(
                source_type="central_system",
                label="Central Water System",
                probability=10,
                evidence=[
                    "Lower confidence for central source based on current alert context.",
                ],
            ),
        ]

    elif origin_scope_type == "distribution_line":
        candidates = [
            _candidate(
                source_type="distribution_system",
                label="Distribution System",
                probability=64 if tier == "ACTION" else 74 if tier == "CRITICAL" else 50,
                evidence=common_evidence + [
                    "Alert metadata indicates the issue likely originates from the distribution line.",
                    "Midstream degradation pattern is more consistent with transport infrastructure than facility-only causes.",
                ],
            ),
            _candidate(
                source_type="building_plumbing",
                label="Building Plumbing",
                probability=24,
                evidence=[
                    "Facility-side contribution remains possible but less likely than distribution-level causes.",
                ],
            ),
            _candidate(
                source_type="central_system",
                label="Central Water System",
                probability=12,
                evidence=[
                    "Current signal pattern is weaker for a fully central-system origin.",
                ],
            ),
        ]

    elif origin_scope_type == "central_system":
        candidates = [
            _candidate(
                source_type="central_system",
                label="Central Water System",
                probability=72 if tier == "ACTION" else 82 if tier == "CRITICAL" else 58,
                evidence=common_evidence + [
                    "Alert metadata points to an upstream centralized source.",
                    "This pattern may affect multiple downstream zones or facilities.",
                ],
            ),
            _candidate(
                source_type="distribution_system",
                label="Distribution System",
                probability=18,
                evidence=[
                    "Distribution infrastructure still remains a secondary possibility.",
                ],
            ),
            _candidate(
                source_type="building_plumbing",
                label="Building Plumbing",
                probability=10,
                evidence=[
                    "Local building plumbing is less likely when the issue is inferred upstream.",
                ],
            ),
        ]

    else:
        # No explicit source hint; infer from parameter behavior
        if parameter_code in {"lead", "copper"}:
            candidates = [
                _candidate(
                    source_type="building_plumbing",
                    label="Building Plumbing",
                    probability=67,
                    evidence=common_evidence + [
                        "Metals risk often aligns with local corrosion or aging internal plumbing.",
                    ],
                ),
                _candidate(
                    source_type="distribution_system",
                    label="Distribution System",
                    probability=23,
                    evidence=["Some contribution from distribution infrastructure is possible."],
                ),
                _candidate(
                    source_type="central_system",
                    label="Central Water System",
                    probability=10,
                    evidence=["Central-source metals contribution appears less likely from current signals."],
                ),
            ]
        elif parameter_code in {"ecoli", "chlorine", "turbidity"}:
            candidates = [
                _candidate(
                    source_type="distribution_system",
                    label="Distribution System",
                    probability=54 if tier == "ACTION" else 66 if tier == "CRITICAL" else 42,
                    evidence=common_evidence + [
                        "Microbial/disinfection patterns frequently indicate line integrity or residual loss issues.",
                    ],
                ),
                _candidate(
                    source_type="central_system",
                    label="Central Water System",
                    probability=28,
                    evidence=["Upstream treatment issues remain possible."],
                ),
                _candidate(
                    source_type="building_plumbing",
                    label="Building Plumbing",
                    probability=18,
                    evidence=["Localized facility conditions may still contribute."],
                ),
            ]
        else:
            candidates = [
                _candidate(
                    source_type="building_plumbing",
                    label="Building Plumbing",
                    probability=48,
                    evidence=common_evidence + [
                        "No strong upstream attribution signal was available; local infrastructure remains a plausible source.",
                    ],
                ),
                _candidate(
                    source_type="distribution_system",
                    label="Distribution System",
                    probability=32,
                    evidence=["Distribution-level contribution is moderately plausible."],
                ),
                _candidate(
                    source_type="central_system",
                    label="Central Water System",
                    probability=20,
                    evidence=["Current evidence is weaker for a centralized source."],
                ),
            ]

    # Sort strongest first
    candidates = sorted(candidates, key=lambda x: x["probability"], reverse=True)

    top = candidates[0]
    confidence_score = top["probability"]
    if confidence_score >= 75:
        confidence_label = "high confidence"
    elif confidence_score >= 55:
        confidence_label = "moderate confidence"
    else:
        confidence_label = "low confidence"

    if top["source_type"] == "building_plumbing":
        headline = "Building infrastructure issue likely"
        summary = "Recent signals suggest the strongest contribution is coming from the facility or building plumbing."
        immediate_actions = [
            "Inspect internal plumbing and fixture endpoints.",
            "Increase sampling at multiple taps inside the facility.",
            "Limit sensitive uses if risk level remains elevated.",
        ]
        follow_up_actions = [
            "Review building pipe age, materials, and corrosion history.",
            "Schedule targeted remediation or plumbing assessment if repeated alerts persist.",
        ]
    elif top["source_type"] == "distribution_system":
        headline = "Distribution system issue likely"
        summary = "Recent signals suggest the strongest contribution is coming from the surrounding distribution network."
        immediate_actions = [
            "Inspect nearby distribution segments for integrity issues.",
            "Increase sampling across adjacent zones.",
            "Notify operations teams for field verification.",
        ]
        follow_up_actions = [
            "Compare neighboring cluster and county patterns.",
            "Assess distribution maintenance records and pressure events.",
        ]
    else:
        headline = "Central supply issue possible"
        summary = "Recent signals suggest the strongest contribution may originate upstream in the centralized supply path."
        immediate_actions = [
            "Review upstream treatment and source quality signals.",
            "Increase cross-zone monitoring.",
            "Notify oversight stakeholders for regional review.",
        ]
        follow_up_actions = [
            "Compare multiple downstream locations for shared anomalies.",
            "Review source-water and treatment logs.",
        ]

    explanation = (
        "Attribution is inferred by combining alert severity, source metadata, parameter behavior, "
        "and site-level context. This output is intended to guide investigation, not replace confirmatory testing."
    )

    return {
        "assessment_type": "inferred",
        "headline": headline,
        "summary": summary,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "candidates": candidates,
        "immediate_actions": immediate_actions,
        "follow_up_actions": follow_up_actions,
        "explanation": explanation,
        "data_sources": [
            "FalilaX alert history",
            "FalilaX measurement-derived alert context",
            "Rule-based source attribution logic",
        ],
    }