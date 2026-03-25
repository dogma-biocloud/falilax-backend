from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.location import Location
from app.services.contamination_prediction_service import predict_location_parameter_risk
from app.services.contamination_spread_service import analyze_contamination_spread
from app.services.recipient_resolution_service import resolve_recipients


def get_recent_open_alerts(
    db: Session,
    *,
    parameter_code: str,
) -> list[Alert]:
    rows = (
        db.query(Alert)
        .filter(Alert.parameter_code == parameter_code)
        .filter(Alert.status.in_(["queued", "sent"]))
        .order_by(Alert.created_at.desc())
        .all()
    )
    return rows


def count_unique_scopes(alerts: list[Alert]) -> int:
    return len({(alert.scope_type, alert.scope_id) for alert in alerts})


def infer_attribution_level(
    *,
    open_alert_count: int,
    unique_scope_count: int,
    spread_status: str,
    predicted_status: str,
) -> tuple[str, float]:
    """
    FalilaX core principle:
    source attribution controls escalation scope.

    Narrowest justified scope first:
    household -> site -> distribution_line -> central_system -> regional
    """

    if open_alert_count == 0:
        return "site", 0.40

    if unique_scope_count <= 1 and spread_status in {"none", "isolated"}:
        if predicted_status in {"attention", "critical"}:
            return "household", 0.75
        return "site", 0.60

    if unique_scope_count == 1 and spread_status == "clustered":
        return "site", 0.68

    if 2 <= unique_scope_count <= 3 and spread_status in {"clustered", "spreading"}:
        return "distribution_line", 0.78

    if unique_scope_count >= 4 and spread_status == "spreading":
        return "central_system", 0.84

    if unique_scope_count >= 6 and spread_status == "spreading" and predicted_status == "critical":
        return "regional", 0.90

    return "site", 0.55


def determine_escalation_level(
    *,
    attribution_level: str,
    predicted_status: str,
) -> str:
    if attribution_level == "household":
        return "household_only"

    if attribution_level == "site":
        return "site_only"

    if attribution_level == "distribution_line":
        return "distribution_line_alert"

    if attribution_level == "central_system":
        return "central_system_alert"

    if attribution_level == "regional":
        return "regional_emergency"

    if predicted_status in {"attention", "critical"}:
        return "site_only"

    return "none"


def determine_target_strategy(
    *,
    attribution_level: str,
) -> tuple[str, str]:
    """
    Returns:
    - target_scope_type
    - target_strategy
    """
    if attribution_level == "household":
        return "location", "notify_household_only"

    if attribution_level == "site":
        return "location", "notify_site_admins_only"

    if attribution_level == "distribution_line":
        return "distribution_line", "notify_all_connected_users"

    if attribution_level == "central_system":
        return "central_system", "notify_all_downstream_users"

    if attribution_level == "regional":
        return "region", "notify_community_and_authorities"

    return "location", "notify_site_admins_only"


def resolve_target_scope_ids(
    db: Session,
    *,
    location_id: int,
    attribution_level: str,
) -> list[int]:
    """
    Resolve the real scope IDs for FalilaX escalation.

    - household/site -> current location_id
    - distribution_line -> location.distribution_line_id
    - central_system -> location.central_system_id
    - regional -> placeholder current location until region tables exist
    """
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if not location:
        return [location_id]

    if attribution_level in {"household", "site"}:
        return [location_id]

    if attribution_level == "distribution_line":
        distribution_line_id = getattr(location, "distribution_line_id", None)
        return [distribution_line_id] if distribution_line_id is not None else [location_id]

    if attribution_level == "central_system":
        central_system_id = getattr(location, "central_system_id", None)
        return [central_system_id] if central_system_id is not None else [location_id]

    if attribution_level == "regional":
        return [location_id]

    return [location_id]


def build_escalation_message(
    *,
    parameter_code: str,
    attribution_level: str,
    escalation_level: str,
    open_alert_count: int,
    unique_scope_count: int,
    spread_status: str,
    predicted_status: str,
    confidence: float,
) -> str:
    confidence_pct = round(confidence * 100)

    if attribution_level == "household":
        return (
            f"{parameter_code} risk appears localized to a household or single endpoint. "
            f"Escalation is restricted to the affected household only. "
            f"Attribution confidence: {confidence_pct}%."
        )

    if attribution_level == "site":
        return (
            f"{parameter_code} risk appears localized to the current site or institution. "
            f"Only site-level stakeholders should be notified at this stage. "
            f"Attribution confidence: {confidence_pct}%."
        )

    if attribution_level == "distribution_line":
        return (
            f"{parameter_code} contamination is likely associated with a shared distribution line. "
            f"Notify all connected users on the affected line. "
            f"Open alerts={open_alert_count}, affected scopes={unique_scope_count}, "
            f"spread_status={spread_status}. Attribution confidence: {confidence_pct}%."
        )

    if attribution_level == "central_system":
        return (
            f"{parameter_code} contamination is likely tied to the central distribution system. "
            f"Notify all downstream connected users and institutions. "
            f"Predicted status={predicted_status}. Attribution confidence: {confidence_pct}%."
        )

    if attribution_level == "regional":
        return (
            f"{parameter_code} contamination shows evidence of broader multi-site or regional spread. "
            f"Community-wide escalation is recommended. "
            f"Attribution confidence: {confidence_pct}%."
        )

    return (
        f"No active community escalation is required for {parameter_code}. "
        f"Open alerts={open_alert_count}, affected scopes={unique_scope_count}, "
        f"spread_status={spread_status}, predicted_status={predicted_status}."
    )


def evaluate_community_alert_escalation(
    db: Session,
    *,
    location_id: int,
    parameter_code: str,
) -> dict[str, Any]:
    alerts = get_recent_open_alerts(
        db,
        parameter_code=parameter_code,
    )

    spread_result = analyze_contamination_spread(
        db,
        parameter_code=parameter_code,
    )

    prediction_result = predict_location_parameter_risk(
        db,
        location_id=location_id,
        parameter_code=parameter_code,
    )

    open_alert_count = len(alerts)
    unique_scope_count = count_unique_scopes(alerts)
    spread_status = spread_result.get("overall_status", "none")
    predicted_status = prediction_result.get("predicted_status", "normal")

    attribution_level, attribution_confidence = infer_attribution_level(
        open_alert_count=open_alert_count,
        unique_scope_count=unique_scope_count,
        spread_status=spread_status,
        predicted_status=predicted_status,
    )

    escalation_level = determine_escalation_level(
        attribution_level=attribution_level,
        predicted_status=predicted_status,
    )

    target_scope_type, target_strategy = determine_target_strategy(
        attribution_level=attribution_level,
    )

    target_scope_ids = resolve_target_scope_ids(
        db,
        location_id=location_id,
        attribution_level=attribution_level,
    )

    message = build_escalation_message(
        parameter_code=parameter_code,
        attribution_level=attribution_level,
        escalation_level=escalation_level,
        open_alert_count=open_alert_count,
        unique_scope_count=unique_scope_count,
        spread_status=spread_status,
        predicted_status=predicted_status,
        confidence=attribution_confidence,
    )

    recipient_result = resolve_recipients(
        db,
        location_id=location_id,
        scope_type=target_scope_type,
        scope_ids=target_scope_ids,
        strategy=target_strategy,
    )

    return {
        "location_id": location_id,
        "parameter_code": parameter_code,
        "open_alert_count": open_alert_count,
        "unique_scope_count": unique_scope_count,
        "spread_status": spread_status,
        "predicted_status": predicted_status,
        "attribution_level": attribution_level,
        "attribution_confidence": attribution_confidence,
        "affected_scope_type": target_scope_type,
        "affected_scope_ids": target_scope_ids,
        "escalation_level": escalation_level,
        "target_strategy": target_strategy,
        "message": message,
        "recipient_resolution": recipient_result,
        "spread_result": spread_result,
        "prediction_result": prediction_result,
    }