from __future__ import annotations

from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.measurement import Measurement
from app.models.parameter_definition import ParameterDefinition
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
    2) Check parameter repository
    3) Validate expected unit
    4) Evaluate thresholds (single-parameter)
    5) Evaluate multi-parameter risk (WaterRiskEngine)
    6) Create/Upsert alert if necessary

    Policy:
    - known active parameters keep incoming quality_flag
    - unknown/inactive parameters are accepted but flagged as 'unmapped'
    - known parameters with wrong unit are accepted but flagged as 'unit_mismatch'
    """

    parameter_def = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.parameter_code == payload.parameter_code)
        .filter(ParameterDefinition.is_active == True)
        .first()
    )

    final_quality_flag = payload.quality_flag

    if parameter_def is None:
        final_quality_flag = "unmapped"
    else:
        expected_unit = (parameter_def.expected_unit or "").strip().lower()
        incoming_unit = (payload.unit or "").strip().lower()

        if expected_unit and incoming_unit and expected_unit != incoming_unit:
            final_quality_flag = "unit_mismatch"

    m = Measurement(
        sample_id=payload.sample_id,
        parameter_code=payload.parameter_code,
        value=payload.value,
        unit=payload.unit,
        qualifier=payload.qualifier,
        method=payload.method,
        measured_at=payload.measured_at,
        source_type=payload.source_type,
        quality_flag=final_quality_flag,
    )

    db.add(m)
    db.commit()
    db.refresh(m)

    raw_result = evaluate_measurement(
        parameter_code=payload.parameter_code,
        value=payload.value,
    )
    tier = TIER_MAP.get(raw_result, "OK")

    risk_result = _evaluate_multi_parameter_risk(db, sample_id=payload.sample_id)

    create_single_param_alert = tier in ("NOTICE", "ACTION")
    create_system_risk_alert = risk_result is not None and (
        risk_result.risk_level in ("NOTICE", "ACTION")
    )

    if create_single_param_alert or create_system_risk_alert:
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
            risk_result=risk_result,
        )

    return m