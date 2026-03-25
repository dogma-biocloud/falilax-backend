from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.services.water_risk_engine import RiskResult  # ok to import; simple dataclass


DEFAULT_DISCLAIMER = (
    "FalilaX provides informational water-quality alerts. "
    "This is not medical advice. If you feel unwell or suspect exposure, "
    "use your local guidance and contact a qualified professional."
)


def _set_if_model_has(values: dict[str, Any], key: str, value: Any) -> None:
    """
    Only set a field if the Alert model has that attribute.
    Prevents breaking when DB columns haven't been added yet.
    """
    if hasattr(Alert, key):
        values[key] = value


def _normalized_tier(tier: str) -> str:
    """
    Keep tiers consistent in storage.
    Escalation should happen later in delivery/formatting logic so
    the dedupe key remains predictable.
    """
    return (tier or "NOTICE").upper()


def create_or_upsert_alert(
    db: Session,
    *,
    user_id: int,
    scope_type: str,
    scope_id: int,
    tier: str,
    parameter_code: str,
    title: str,
    message: str,
    # allow status to be passed (default queued)
    status: str = "queued",
    # delivery
    delivery_channel: str = "in_app",
    recipient: Optional[str] = None,
    scheduled_for: Optional[datetime] = None,
    # attribution
    origin_scope_type: str = "unknown",
    origin_scope_id: Optional[int] = None,
    # geo
    cluster_code: Optional[str] = None,
    region_code: Optional[str] = None,
    county_code: Optional[str] = None,
    # location context (optional)
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
    # safety
    confidence: str = "suspected",
    disclaimer: Optional[str] = None,
    # measured context (optional)
    measured_value: Optional[float] = None,
    unit: Optional[str] = None,
    threshold: Optional[float] = None,
    threshold_kind: Optional[str] = None,  # "max" | "min" | "range" etc
    # multi-parameter system risk output (optional)
    risk_result: Optional[RiskResult] = None,
) -> None:
    """
    Insert an alert; if it already exists (dedupe key), update it instead.

    Existing alert branch behavior:
      - occurrence_count += 1
      - last_seen_at = now()
      - status reset to queued so worker can pick it up again
      - sent_at cleared if column exists
      - prior delivery error cleared if columns exist

    Dedupe key:
      (user_id, scope_type, scope_id, tier, parameter_code)

    Note:
      Tier escalation is intentionally NOT done here, because tier is part of the
      dedupe key. Escalation is better handled in delivery/formatting logic after load.
    """

    effective_disclaimer = disclaimer or DEFAULT_DISCLAIMER
    effective_tier = _normalized_tier(tier)

    values: dict[str, Any] = {
        "user_id": user_id,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "tier": effective_tier,
        "parameter_code": parameter_code,
        "title": title,
        "message": message,
        "status": status,
        "last_seen_at": func.now(),
        "occurrence_count": 1,
        "delivery_channel": delivery_channel,
        "recipient": recipient,
        "scheduled_for": scheduled_for,
        "origin_scope_type": origin_scope_type,
        "origin_scope_id": origin_scope_id,
        "cluster_code": cluster_code,
        "region_code": region_code,
        "county_code": county_code,
        "confidence": confidence,
        "disclaimer": effective_disclaimer,
    }

    # Optional measured context
    _set_if_model_has(values, "measured_value", measured_value)
    _set_if_model_has(values, "unit", unit)
    _set_if_model_has(values, "threshold", threshold)
    _set_if_model_has(values, "threshold_kind", threshold_kind)

    # Optional location context
    _set_if_model_has(values, "location_label", location_label)
    _set_if_model_has(values, "address_line1", address_line1)
    _set_if_model_has(values, "address_line2", address_line2)
    _set_if_model_has(values, "city", city)
    _set_if_model_has(values, "state_region", state_region)
    _set_if_model_has(values, "postal_code", postal_code)
    _set_if_model_has(values, "country", country)
    _set_if_model_has(values, "latitude", latitude)
    _set_if_model_has(values, "longitude", longitude)
    _set_if_model_has(values, "plus_code", plus_code)
    _set_if_model_has(values, "landmark", landmark)
    _set_if_model_has(values, "directions_hint", directions_hint)

    # Optional risk payload
    payload: Optional[dict[str, Any]] = None
    if risk_result is not None:
        payload = {
            "risk_level": risk_result.risk_level,
            "message": risk_result.message,
            "trigger_parameters": list(risk_result.trigger_parameters),
        }
        _set_if_model_has(values, "risk_payload", payload)
        _set_if_model_has(values, "system_risk_level", risk_result.risk_level)

    stmt = insert(Alert).values(**values)

    # Existing alert branch: requeue + refresh alert context
    set_: dict[str, Any] = {
        "occurrence_count": Alert.occurrence_count + 1,
        "last_seen_at": func.now(),
        "title": title,
        "message": message,
        # IMPORTANT: reset to queued so worker picks it up again
        "status": "queued",
        "delivery_channel": delivery_channel,
        "recipient": recipient,
        "scheduled_for": scheduled_for,
        "origin_scope_type": origin_scope_type,
        "origin_scope_id": origin_scope_id,
        "cluster_code": cluster_code,
        "region_code": region_code,
        "county_code": county_code,
        "confidence": confidence,
        "disclaimer": effective_disclaimer,
    }

    # Keep stored tier normalized, but do not escalate here
    if hasattr(Alert, "tier"):
        set_["tier"] = effective_tier

    # Optional delivery-state reset fields
    if hasattr(Alert, "sent_at"):
        set_["sent_at"] = None

    if hasattr(Alert, "last_error"):
        set_["last_error"] = None

    if hasattr(Alert, "last_error_at"):
        set_["last_error_at"] = None

    if hasattr(Alert, "delivery_attempts"):
        set_["delivery_attempts"] = 0

    # Optional measured context updates
    if hasattr(Alert, "measured_value"):
        set_["measured_value"] = measured_value
    if hasattr(Alert, "unit"):
        set_["unit"] = unit
    if hasattr(Alert, "threshold"):
        set_["threshold"] = threshold
    if hasattr(Alert, "threshold_kind"):
        set_["threshold_kind"] = threshold_kind

    # Optional location context updates
    if hasattr(Alert, "location_label"):
        set_["location_label"] = location_label
    if hasattr(Alert, "address_line1"):
        set_["address_line1"] = address_line1
    if hasattr(Alert, "address_line2"):
        set_["address_line2"] = address_line2
    if hasattr(Alert, "city"):
        set_["city"] = city
    if hasattr(Alert, "state_region"):
        set_["state_region"] = state_region
    if hasattr(Alert, "postal_code"):
        set_["postal_code"] = postal_code
    if hasattr(Alert, "country"):
        set_["country"] = country
    if hasattr(Alert, "latitude"):
        set_["latitude"] = latitude
    if hasattr(Alert, "longitude"):
        set_["longitude"] = longitude
    if hasattr(Alert, "plus_code"):
        set_["plus_code"] = plus_code
    if hasattr(Alert, "landmark"):
        set_["landmark"] = landmark
    if hasattr(Alert, "directions_hint"):
        set_["directions_hint"] = directions_hint

    # Optional risk payload updates
    if risk_result is not None:
        if hasattr(Alert, "risk_payload"):
            set_["risk_payload"] = payload
        if hasattr(Alert, "system_risk_level"):
            set_["system_risk_level"] = risk_result.risk_level

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "scope_type", "scope_id", "tier", "parameter_code"],
        set_=set_,
    )

    db.execute(stmt)
    db.commit()