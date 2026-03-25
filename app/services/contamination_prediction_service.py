from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.models.measurement import Measurement
from app.models.parameter_definition import ParameterDefinition
from app.models.water_sample import WaterSample


def get_recent_measurements_for_location(
    db: Session,
    *,
    location_id: int,
    parameter_code: str,
    limit: int = 20,
) -> list[Measurement]:
    rows = (
        db.query(Measurement)
        .join(WaterSample, Measurement.sample_id == WaterSample.id)
        .filter(WaterSample.location_id == location_id)
        .filter(Measurement.parameter_code == parameter_code)
        .order_by(Measurement.measured_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def get_parameter_definition(
    db: Session,
    *,
    parameter_code: str,
) -> ParameterDefinition | None:
    return (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.parameter_code == parameter_code)
        .filter(ParameterDefinition.is_active.is_(True))
        .first()
    )


def classify_predicted_status(
    *,
    predicted_value: float,
    param: ParameterDefinition | None,
) -> str:
    if not param:
        return "normal"

    if param.critical_min is not None and predicted_value < param.critical_min:
        return "critical"

    if param.critical_max is not None and predicted_value > param.critical_max:
        return "critical"

    if param.warn_min is not None and predicted_value < param.warn_min:
        return "attention"

    if param.warn_max is not None and predicted_value > param.warn_max:
        return "attention"

    return "normal"


def build_prediction_features(measurements: list[Measurement]) -> dict[str, Any]:
    values = [m.value for m in measurements if m.value is not None]

    if not values:
        return {
            "count": 0,
            "latest_value": None,
            "average_value": None,
            "trend_delta": None,
            "momentum": "stable",
        }

    latest_value = values[-1]
    average_value = mean(values)

    trend_delta = 0.0
    if len(values) >= 2:
        trend_delta = values[-1] - values[0]

    if trend_delta > 0:
        momentum = "up"
    elif trend_delta < 0:
        momentum = "down"
    else:
        momentum = "stable"

    return {
        "count": len(values),
        "latest_value": latest_value,
        "average_value": average_value,
        "trend_delta": trend_delta,
        "momentum": momentum,
    }


def predict_next_value(
    *,
    latest_value: float | None,
    average_value: float | None,
    trend_delta: float | None,
    count: int,
) -> float | None:
    if latest_value is None:
        return None

    if count < 3 or average_value is None or trend_delta is None:
        return latest_value

    slope_component = trend_delta / max(count - 1, 1)

    # Simple forecast:
    # next value leans mostly on latest, with small influence from slope and mean.
    predicted = (0.65 * latest_value) + (0.25 * (latest_value + slope_component)) + (0.10 * average_value)
    return predicted


def build_confidence(
    *,
    count: int,
    trend_delta: float | None,
) -> float:
    base = min(count / 20.0, 1.0)

    if trend_delta is None:
        return round(base * 0.5, 2)

    trend_bonus = min(abs(trend_delta) / 10.0, 0.2)
    return round(min(base + trend_bonus, 0.99), 2)


def predict_location_parameter_risk(
    db: Session,
    *,
    location_id: int,
    parameter_code: str,
) -> dict[str, Any]:
    measurements = get_recent_measurements_for_location(
        db,
        location_id=location_id,
        parameter_code=parameter_code,
    )

    features = build_prediction_features(measurements)

    predicted_value = predict_next_value(
        latest_value=features["latest_value"],
        average_value=features["average_value"],
        trend_delta=features["trend_delta"],
        count=features["count"],
    )

    param = get_parameter_definition(
        db,
        parameter_code=parameter_code,
    )

    predicted_status = "normal"
    if predicted_value is not None:
        predicted_status = classify_predicted_status(
            predicted_value=predicted_value,
            param=param,
        )

    confidence = build_confidence(
        count=features["count"],
        trend_delta=features["trend_delta"],
    )

    return {
        "location_id": location_id,
        "parameter_code": parameter_code,
        "expected_unit": param.expected_unit if param else None,
        "history_count": features["count"],
        "latest_value": features["latest_value"],
        "average_value": features["average_value"],
        "trend_delta": features["trend_delta"],
        "momentum": features["momentum"],
        "predicted_next_value": predicted_value,
        "predicted_status": predicted_status,
        "confidence": confidence,
    }