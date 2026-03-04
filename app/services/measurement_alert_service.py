from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.services.water_risk_engine import WaterRiskEngine, RiskResult

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertCreateResult:
    created: bool
    alert_id: Optional[int]
    reason: str
    risk_result: Optional[RiskResult]


class MeasurementAlertService:
    """
    Creates queued alerts from incoming measurements.

    - Runs WaterRiskEngine (multi-parameter).
    - If a system-risk rule triggers, we create a queued alert (status='queued').
    - The AlertDeliveryWorker will format + deliver it.
    """

    def __init__(self) -> None:
        self._risk_engine = WaterRiskEngine()

    def create_alert_from_measurement(
        self,
        db: Session,
        *,
        user_id: int,
        scope_type: str,
        scope_id: int,
        parameters: Dict[str, float],
        # Optional location context (if you have it from measurement/site tables)
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
        # Optional: if you want to attach measurement linkage later
        measurement_id: Optional[int] = None,
        source_kind: Optional[str] = None,  # "central" | "line" | "site"
    ) -> AlertCreateResult:
        # 1) Multi-parameter risk evaluation
        risk_result = self._risk_engine.evaluate(parameters)
        if not risk_result:
            return AlertCreateResult(
                created=False,
                alert_id=None,
                reason="No multi-parameter risk detected",
                risk_result=None,
            )

        tier = (risk_result.risk_level or "NOTICE").upper()

        # 2) Choose a representative parameter_code for the alert row
        #    (we store one code in DB, but the formatter can show the whole system-risk block)
        parameter_code = risk_result.trigger_parameters[0] if risk_result.trigger_parameters else "unknown"

        # 3) Create queued alert (delivery worker will format message + set status=sent)
        alert = Alert(
            user_id=user_id,
            scope_type=scope_type,
            scope_id=scope_id,
            tier=tier,
            parameter_code=parameter_code,
            message=risk_result.message,
            confidence="suspected",
            status="queued",
            # location fields
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

        # Optional fields if your Alert model has them (safe no-op if not present)
        if measurement_id is not None and hasattr(alert, "measurement_id"):
            try:
                setattr(alert, "measurement_id", measurement_id)
            except Exception:
                pass

        if source_kind and hasattr(alert, "source_kind"):
            try:
                setattr(alert, "source_kind", source_kind)
            except Exception:
                pass

        db.add(alert)
        db.commit()
        db.refresh(alert)

        log.info(
            "Queued alert from measurement",
            extra={
                "alert_id": alert.id,
                "tier": tier,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "parameter_code": parameter_code,
                "trigger_parameters": list(risk_result.trigger_parameters),
            },
        )

        return AlertCreateResult(
            created=True,
            alert_id=alert.id,
            reason="Multi-parameter risk detected; alert queued",
            risk_result=risk_result,
        )