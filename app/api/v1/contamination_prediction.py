from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.contamination_prediction_service import (
    predict_location_parameter_risk,
)

router = APIRouter(prefix="/contamination-prediction", tags=["Contamination Prediction"])


@router.get("/{location_id}/{parameter_code}")
def get_contamination_prediction(
    location_id: int,
    parameter_code: str,
    db: Session = Depends(get_db),
):
    return predict_location_parameter_risk(
        db=db,
        location_id=location_id,
        parameter_code=parameter_code,
    )