# app/services/alert_engine.py

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.services.threshold_rules import DEFAULT_THRESHOLDS


DEFAULT_DISCLAIMER = (
    "FalilaX provides informational water-quality alerts only. Not medical advice. "
    "If you believe there is immediate danger, contact local authorities or a qualified professional."
)


def evaluate_measurement(parameter_code: str, value: float) -> str:
    rules = DEFAULT_THRESHOLDS.get(parameter_code)
    if not rules:
        return "NORMAL"

    if "critical_min" in rules and value < rules["critical_min"]:
        return "ACTION_RECOMMENDED"
    if "critical_max" in rules and value > rules["critical_max"]:
        return "ACTION_RECOMMENDED"

    if "warn_min" in rules and value < rules["warn_min"]:
        return "ATTENTION"
    if "warn_max" in rules and value > rules["warn_max"]:
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


def choose_confidence(*, eval_result: str) -> str:
    """
    Simple starter logic:
      - ACTION => 'confirmed' (stronger signal)
      - NOTICE => 'suspected'
    You can later connect this to sensor reliability / repeat reads / lab confirmation.
    """
    if eval_result == "ACTION_RECOMMENDED":
        return "confirmed"
    return "suspected"


def upsert_alert(
    db: Session,
    *,
    user_id: int,
    scope_type: str,
    scope_id: int,
    tier: str,
    parameter_code: str,
    title: str,
    message: str,
    # delivery
    delivery_channel: str = "in_app",   # in_app/email/sms
    recipient: Optional[str] = None,    # email address or phone number
    scheduled_for: Optional[datetime] = None,
    # attribution
    origin_scope_type: str = "unknown",  # central_system/distribution_line/site/unknown
    origin_scope_id: Optional[int] = None,
    # geo
    cluster_code: Optional[str] = None,
    region_code: Optional[str] = None,
    county_code: Optional[str] = None,
    # safety
    confidence: str = "suspected",
    disclaimer: Optional[str] = None,
) -> None:
    """
    Insert alert; if it already exists (dedupe key), update it instead:
      - occurrence_count += 1
      - last_seen_at = now()
      - title/message refreshed
      - status returned to queued (so delivery worker can send again if needed)
    """

    if disclaimer is None:
        disclaimer = DEFAULT_DISCLAIMER

    stmt = insert(Alert).values(
        user_id=user_id,
        scope_type=scope_type,
        scope_id=scope_id,
        tier=tier,
        parameter_code=parameter_code,
        title=title,
        message=message,
        status="queued",
        last_seen_at=func.now(),
        # delivery
        delivery_channel=delivery_channel,
        recipient=recipient,
        scheduled_for=scheduled_for,
        # attribution
        origin_scope_type=origin_scope_type,
        origin_scope_id=origin_scope_id,
        # geo
        cluster_code=cluster_code,
        region_code=region_code,
        county_code=county_code,
        # safety
        confidence=confidence,
        disclaimer=disclaimer,
    )

    # uses DB unique index ux_alerts_dedupe (user_id, scope_type, scope_id, tier, parameter_code)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "scope_type", "scope_id", "tier", "parameter_code"],
        set_={
            "occurrence_count": Alert.occurrence_count + 1,
            "last_seen_at": func.now(),
            "title": title,
            "message": message,
            "status": "queued",
            # keep latest routing/attribution if caller provided them
            "delivery_channel": delivery_channel,
            "recipient": recipient,
            "scheduled_for": scheduled_for,
            "origin_scope_type": origin_scope_type,
            "origin_scope_id": origin_scope_id,
            "cluster_code": cluster_code,
            "region_code": region_code,
            "county_code": county_code,
            "confidence": confidence,
            "disclaimer": disclaimer,
        },
    )

    db.execute(stmt)
    db.commit()


def process_measurement_for_alerts(
    db: Session,
    *,
    user_id: int,
    sample_id: int,
    parameter_code: str,
    value: float,
    # attribution inputs (pass these from your measurement pipeline)
    origin_scope_type: str = "unknown",
    origin_scope_id: Optional[int] = None,
    cluster_code: Optional[str] = None,
    region_code: Optional[str] = None,
    county_code: Optional[str] = None,
    # delivery defaults (later: choose based on subscriptions/preferences)
    delivery_channel: str = "in_app",
    recipient: Optional[str] = None,
    scheduled_for: Optional[datetime] = None,
) -> None:
    eval_result = evaluate_measurement(parameter_code, value)
    tier = map_eval_to_tier(eval_result)

    if not tier:
        return

    # messaging tuned for calm, non-alarmist style
    if tier == "ACTION":
        title = f"Water check: {parameter_code} needs action"
        msg_core = f"Measured {parameter_code}={value}. This is outside safe limits."
    else:
        title = f"Water check: {parameter_code} needs attention"
        msg_core = f"Measured {parameter_code}={value}. This is outside the preferred range."

    # source attribution sentence
    if origin_scope_type != "unknown":
        src = f"Suspected source: {origin_scope_type}"
        if origin_scope_id is not None:
            src += f" (id={origin_scope_id})"
        msg_core += f" {src}."

    # geo tagging sentence
    geo_bits = [b for b in [cluster_code, region_code, county_code] if b]
    if geo_bits:
        msg_core += f" Area tags: {', '.join(geo_bits)}."

    confidence = choose_confidence(eval_result=eval_result)

    upsert_alert(
        db,
        user_id=user_id,
        scope_type="water_sample",
        scope_id=sample_id,
        tier=tier,
        parameter_code=parameter_code,
        title=title,
        message=msg_core,
        delivery_channel=delivery_channel,
        recipient=recipient,
        scheduled_for=scheduled_for,
        origin_scope_type=origin_scope_type,
        origin_scope_id=origin_scope_id,
        cluster_code=cluster_code,
        region_code=region_code,
        county_code=county_code,
        confidence=confidence,
    )