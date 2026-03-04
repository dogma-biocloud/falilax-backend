from __future__ import annotations

from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.measurement import Measurement
from app.schemas.measurement import MeasurementCreate
from app.services.alert_service import create_or_upsert_alert
from app.services.threshold_rules import evaluate_measurement
from app.services.water_risk_engine import WaterRiskEngine, RiskResult

# Calm tier mapping
# evaluator returns: normal / attention / critical
# we map to operational tiers
TIER_MAP = {
    "normal": "OK",
    "attention": "NOTICE",
    "critical": "ACTION",
}


def get_all_measurements(db: Session):
    return db.query(Measurement).all()


def _build_alert_text(parameter_code: str, value: float, tier: str) -> tuple[str, str]:
    """
    Returns (title, message) using calm, non-alarming tone.
    """
    p = (parameter_code or "parameter").upper()

    if tier == "NOTICE":
        title = f"NOTICE: {p}"
        message = f"{parameter_code} out of preferred range"
        return title, message

    if tier == "ACTION":
        title = f"ACTION: {p}"
        message = f"{parameter_code} out of range"
        return title, message

    return "", ""


def _collect_latest_parameters_for_sample(
    db: Session,
    *,
    sample_id: int,
) -> Dict[str, float]:
    """
    Build a dict of {parameter_code: latest_value} for this sample.

    We keep it simple and deterministic:
    - query all measurements for the sample ordered by created_at/id desc
    - keep the first seen per parameter_code
    """
    params: Dict[str, float] = {}

    q = (
        select(Measurement)
        .where(Measurement.sample_id == sample_id)
        .order_by(Measurement.id.desc())
    )
    rows = db.execute(q).scalars().all()

    for m in rows:
        code = (getattr(m, "parameter_code", None) or "").strip().lower()
        val = getattr(m, "value", None)

        if not code:
            continue
        if val is None:
            continue

        # keep the most recent value per parameter
        if code not in params:
            try:
                params[code] = float(val)
            except Exception:
                continue

    return params


def _evaluate_multi_parameter_risk(
    db: Session,
    *,
    sample_id: int,
) -> RiskResult | None:
    """
    Run WaterRiskEngine on the latest parameter snapshot for the sample.
    Returns RiskResult or None.
    """
    params = _collect_latest_parameters_for_sample(db, sample_id=sample_id)
    if not params:
        return None

    engine = WaterRiskEngine()
    return engine.evaluate(params)


def create_measurement(db: Session, payload: MeasurementCreate):
    """
    1) Save measurement
    2) Evaluate thresholds (single-parameter)
    3) Evaluate multi-parameter risk (WaterRiskEngine)
    4) Create/Upsert alert if necessary
    """

    m = Measurement(
        sample_id=payload.sample_id,
        parameter_code=payload.parameter_code,
        value=payload.value,
        unit=payload.unit,
        qualifier=payload.qualifier,
        method=payload.method,
    )

    db.add(m)
    db.commit()
    db.refresh(m)

    # 1) Single-parameter threshold evaluation
    raw_result = evaluate_measurement(
        parameter_code=payload.parameter_code,
        value=payload.value,
    )
    tier = TIER_MAP.get(raw_result, "OK")

    # 2) Multi-parameter risk evaluation (based on latest values in this sample)
    # NOTE: safe even if only 1 parameter exists (engine will usually return None)
    risk_result = _evaluate_multi_parameter_risk(db, sample_id=payload.sample_id)

    # Decide: create alert if either single-parameter says NOTICE/ACTION OR system risk exists
    create_single_param_alert = tier in ("NOTICE", "ACTION")
    create_system_risk_alert = risk_result is not None and (risk_result.risk_level in ("NOTICE", "ACTION"))

    if create_single_param_alert or create_system_risk_alert:
        # If single-param tier is OK but system risk is NOTICE/ACTION, promote tier to system tier
        final_tier = tier
        if final_tier == "OK" and risk_result is not None:
            final_tier = risk_result.risk_level

        title, message = _build_alert_text(
            payload.parameter_code,
            payload.value,
            final_tier,
        )

        create_or_upsert_alert(
            db,
            user_id=payload.user_id,
            scope_type="water_sample",
            scope_id=payload.sample_id,
            tier=final_tier,
            parameter_code=payload.parameter_code,
            title=title,
            message=message,
            status="queued",
            measured_value=payload.value,
            unit=payload.unit,
            # NEW: pass system risk result so AlertFormatter can include the block
            risk_result=risk_result,
        )

    return m