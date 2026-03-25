from sqlalchemy.orm import Session

from app.models.parameter_definition import ParameterDefinition


def evaluate_measurement(
    db: Session,
    parameter_code: str,
    value: float,
) -> str:
    """
    Evaluate a normalized measurement using threshold values stored
    in parameter_definitions.

    Expected:
    - parameter_code is the canonical parameter code
    - value is already normalized to the canonical unit

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

    # Critical first
    if param.critical_min is not None and value < param.critical_min:
        return "critical"

    if param.critical_max is not None and value > param.critical_max:
        return "critical"

    # Warning next
    if param.warn_min is not None and value < param.warn_min:
        return "attention"

    if param.warn_max is not None and value > param.warn_max:
        return "attention"

    return "normal"