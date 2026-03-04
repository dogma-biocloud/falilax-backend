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
    # NEW: allow status to be passed (default queued)
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
    # safety
    confidence: str = "suspected",
    disclaimer: Optional[str] = None,
    # NEW: measured context (optional)
    measured_value: Optional[float] = None,
    unit: Optional[str] = None,
    threshold: Optional[float] = None,
    threshold_kind: Optional[str] = None,  # "max" | "min" | "range" etc
    # NEW: multi-parameter system risk output (optional)
    risk_result: Optional[RiskResult] = None,
) -> None:
    """
    Insert an alert; if it already exists (dedupe key), update it instead:
      - occurrence_count += 1
      - last_seen_at = now()
      - keep status queued (so delivery worker can pick it up)
    Dedupe key: (user_id, scope_type, scope_id, tier, parameter_code)
    """

    values: dict[str, Any] = {
        "user_id": user_id,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "tier": tier,
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
        "disclaimer": disclaimer or DEFAULT_DISCLAIMER,
    }

    # Optional measured context (only if columns exist)
    _set_if_model_has(values, "measured_value", measured_value)
    _set_if_model_has(values, "unit", unit)
    _set_if_model_has(values, "threshold", threshold)
    _set_if_model_has(values, "threshold_kind", threshold_kind)

    # Optional risk payload (only if column exists)
    if risk_result is not None:
        payload = {
            "risk_level": risk_result.risk_level,
            "message": risk_result.message,
            "trigger_parameters": list(risk_result.trigger_parameters),
        }
        _set_if_model_has(values, "risk_payload", payload)
        _set_if_model_has(values, "system_risk_level", risk_result.risk_level)

    stmt = insert(Alert).values(**values)

    # Build conflict update map
    set_: dict[str, Any] = {
        "occurrence_count": Alert.occurrence_count + 1,
        "last_seen_at": func.now(),
        "title": title,
        "message": message,
        # IMPORTANT: keep queued so worker picks it up again
        "status": status,
        "delivery_channel": delivery_channel,
        "recipient": recipient,
        "scheduled_for": scheduled_for,
        "origin_scope_type": origin_scope_type,
        "origin_scope_id": origin_scope_id,
        "cluster_code": cluster_code,
        "region_code": region_code,
        "county_code": county_code,
        "confidence": confidence,
        "disclaimer": disclaimer or DEFAULT_DISCLAIMER,
    }

    # Optional measured context updates (only if columns exist)
    if hasattr(Alert, "measured_value"):
        set_["measured_value"] = measured_value
    if hasattr(Alert, "unit"):
        set_["unit"] = unit
    if hasattr(Alert, "threshold"):
        set_["threshold"] = threshold
    if hasattr(Alert, "threshold_kind"):
        set_["threshold_kind"] = threshold_kind

    # Optional risk payload updates (only if columns exist)
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