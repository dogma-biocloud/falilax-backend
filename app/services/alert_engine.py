# app/services/alert_engine.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.parameter_definition import ParameterDefinition
from app.services.alert_service import create_or_upsert_alert
from app.services.water_risk_engine import WaterRiskEngine, RiskResult


DEFAULT_DISCLAIMER = (
    "FalilaX provides informational water-quality alerts only. Not medical advice. "
    "If you believe there is immediate danger, contact local authorities or a qualified professional."
)


def _get_parameter_definition(
    db: Session,
    parameter_code: str,
) -> Optional[ParameterDefinition]:
    return (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.parameter_code == parameter_code)
        .filter(ParameterDefinition.is_active == True)
        .first()
    )


def evaluate_measurement(db: Session, parameter_code: str, value: float) -> str:
    param = _get_parameter_definition(db, parameter_code)

    if not param:
        return "NORMAL"

    if param.critical_min is not None and value < param.critical_min:
        return "ACTION_RECOMMENDED"
    if param.critical_max is not None and value > param.critical_max:
        return "ACTION_RECOMMENDED"

    if param.warn_min is not None and value < param.warn_min:
        return "ATTENTION"
    if param.warn_max is not None and value > param.warn_max:
        return "ATTENTION"

    return "NORMAL"


def map_eval_to_tier(eval_result: str) -> str | None:
    if eval_result == "NORMAL":
        return None
    if eval_result == "ATTENTION":
        return "NOTICE"
    if eval_result == "ACTION_RECOMMENDED":
        return "ACTION"
    return "NOTICE"


def choose_confidence(*, eval_result: str, risk_result: Optional[RiskResult] = None) -> str:
    if risk_result is not None and risk_result.risk_level in ("ACTION", "CRITICAL"):
        return "confirmed"
    if eval_result == "ACTION_RECOMMENDED":
        return "confirmed"
    return "suspected"


def _threshold_info(
    db: Session,
    parameter_code: str,
    value: float,
) -> tuple[Optional[float], Optional[str]]:
    """
    Returns (threshold_value, threshold_kind) where kind is 'min' or 'max'
    depending on which side was breached. If unknown, (None, None).
    """
    param = _get_parameter_definition(db, parameter_code)

    if not param:
        return None, None

    if param.critical_min is not None and value < param.critical_min:
        return float(param.critical_min), "min"
    if param.critical_max is not None and value > param.critical_max:
        return float(param.critical_max), "max"

    if param.warn_min is not None and value < param.warn_min:
        return float(param.warn_min), "min"
    if param.warn_max is not None and value > param.warn_max:
        return float(param.warn_max), "max"

    return None, None


def _risk_tier_to_alert_tier(risk_level: str) -> str:
    rl = (risk_level or "").upper()
    if rl == "CRITICAL":
        return "CRITICAL"
    if rl == "ACTION":
        return "ACTION"
    if rl == "NOTICE":
        return "NOTICE"
    return "NOTICE"


def process_measurement_for_alerts(
    db: Session,
    *,
    user_id: int,
    sample_id: int,
    parameter_code: str,
    value: float,
    unit: Optional[str] = None,
    origin_scope_type: str = "unknown",
    origin_scope_id: Optional[int] = None,
    cluster_code: Optional[str] = None,
    region_code: Optional[str] = None,
    county_code: Optional[str] = None,
    delivery_channel: str = "in_app",
    recipient: Optional[str] = None,
    scheduled_for: Optional[datetime] = None,
    location_label: Optional[str] = None,
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    state_region: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    plus_code: Optional[str] = None,
    landmark: Optional[str] = None,
    directions_hint: Optional[str] = None,
) -> None:
    # Threshold-based evaluation from database
    eval_result = evaluate_measurement(db, parameter_code, value)
    threshold_tier = map_eval_to_tier(eval_result)

    # Risk-engine evaluation
    risk_result = WaterRiskEngine().evaluate({parameter_code.lower(): value})
    risk_tier = _risk_tier_to_alert_tier(risk_result.risk_level) if risk_result else None

    severity_rank = {"NOTICE": 1, "ACTION": 2, "CRITICAL": 3}
    candidates = [t for t in [threshold_tier, risk_tier] if t]
    if not candidates:
        return

    tier = max(candidates, key=lambda t: severity_rank.get(t, 0))

    threshold_value, threshold_kind = _threshold_info(db, parameter_code, value)
    confidence = choose_confidence(eval_result=eval_result, risk_result=risk_result)

    unit_txt = f" {unit}" if unit else ""

    if risk_result is not None and tier == _risk_tier_to_alert_tier(risk_result.risk_level):
        if tier == "CRITICAL":
            title = f"Water check: {parameter_code} is critical"
        elif tier == "ACTION":
            title = f"Water check: {parameter_code} needs action"
        else:
            title = f"Water check: {parameter_code} needs attention"

        msg_core = f"Measured {parameter_code}={value}{unit_txt}. {risk_result.message}"
    else:
        if tier == "CRITICAL":
            title = f"Water check: {parameter_code} is critical"
            msg_core = f"Measured {parameter_code}={value}{unit_txt}. This is far outside safe limits."
        elif tier == "ACTION":
            title = f"Water check: {parameter_code} needs action"
            msg_core = f"Measured {parameter_code}={value}{unit_txt}. This is outside safe limits."
        else:
            title = f"Water check: {parameter_code} needs attention"
            msg_core = f"Measured {parameter_code}={value}{unit_txt}. This is outside the preferred range."

    if origin_scope_type and origin_scope_type != "unknown":
        src = f"Suspected source: {origin_scope_type}"
        if origin_scope_id is not None:
            src += f" (id={origin_scope_id})"
        msg_core += f" {src}."

    geo_bits = [b for b in [cluster_code, region_code, county_code, state_region, country] if b]
    if geo_bits:
        msg_core += f" Area tags: {', '.join(geo_bits)}."

    create_or_upsert_alert(
        db,
        user_id=user_id,
        scope_type="water_sample",
        scope_id=sample_id,
        tier=tier,
        parameter_code=parameter_code,
        title=title,
        message=msg_core,
        status="queued",
        delivery_channel=delivery_channel,
        recipient=recipient,
        scheduled_for=scheduled_for,
        origin_scope_type=origin_scope_type,
        origin_scope_id=origin_scope_id,
        cluster_code=cluster_code,
        region_code=region_code,
        county_code=county_code,
        confidence=confidence,
        disclaimer=DEFAULT_DISCLAIMER,
        measured_value=value,
        unit=unit,
        threshold=threshold_value,
        threshold_kind=threshold_kind,
        risk_result=risk_result,
        location_label=location_label,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state_region=state_region,
        postal_code=postal_code,
        country=country,
        latitude=latitude,
        longitude=longitude,
        plus_code=plus_code,
        landmark=landmark,
        directions_hint=directions_hint,
    )