from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.community_alert_escalation_service import (
    evaluate_community_alert_escalation,
)

router = APIRouter(
    prefix="/community-alert-escalation",
    tags=["Community Alert Escalation"],
)


@router.get("/{location_id}/{parameter_code}")
def get_community_alert_escalation(
    location_id: int,
    parameter_code: str,
    db: Session = Depends(get_db),
):
    return evaluate_community_alert_escalation(
        db=db,
        location_id=location_id,
        parameter_code=parameter_code,
    )