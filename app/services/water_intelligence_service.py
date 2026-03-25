from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.community_alert_escalation_service import (
    evaluate_community_alert_escalation,
)
from app.services.contamination_prediction_service import (
    predict_location_parameter_risk,
)
from app.services.contamination_spread_service import (
    analyze_contamination_spread,
    get_recent_abnormal_sites,
)


def build_water_intelligence_snapshot(
    db: Session,
    *,
    location_id: int,
    parameter_code: str,
) -> dict[str, Any]:
    spread_result = analyze_contamination_spread(
        db=db,
        parameter_code=parameter_code,
    )

    prediction_result = predict_location_parameter_risk(
        db=db,
        location_id=location_id,
        parameter_code=parameter_code,
    )

    escalation_result = evaluate_community_alert_escalation(
        db=db,
        location_id=location_id,
        parameter_code=parameter_code,
    )

    abnormal_sites = get_recent_abnormal_sites(
        db=db,
        parameter_code=parameter_code,
        limit=50,
    )

    return {
        "location_id": location_id,
        "parameter_code": parameter_code,
        "spread": spread_result,
        "prediction": prediction_result,
        "escalation": escalation_result,
        "recent_abnormal_sites": [site.__dict__ for site in abnormal_sites],
    }