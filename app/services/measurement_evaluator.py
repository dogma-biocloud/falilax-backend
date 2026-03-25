from sqlalchemy.orm import Session

from app.models.parameter_definition import ParameterDefinition


def evaluate_measurement(
    db: Session,
    parameter_code: str,
    value: float,
    unit: str | None = None,
) -> str:
    """
    Evaluate a normalized measurement using threshold values stored
    in parameter_definitions.

    Returns:
        "normal"
        "attention"
        "critical"
    """

    param = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.parameter_code == parameter_code)
        .filter(ParameterDefinition.is_active.is_(True))
        .first()
    )

    if not param:
        return "normal"

    if not param.alerts_enabled:
        return "normal"

    # Normalize unit comparison to avoid case mismatches
    if unit and param.expected_unit:
        if unit.strip().lower() != param.expected_unit.strip().lower():
            return "normal"

    # Critical thresholds
    if param.critical_min is not None and value < param.critical_min:
        return "critical"

    if param.critical_max is not None and value > param.critical_max:
        return "critical"

    # Warning thresholds
    if param.warn_min is not None and value < param.warn_min:
        return "attention"

    if param.warn_max is not None and value > param.warn_max:
        return "attention"

    return "normal"