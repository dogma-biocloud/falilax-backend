from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.alert_dispatch_service import execute_alert_dispatch

router = APIRouter(
    prefix="/alert-dispatch",
    tags=["Alert Dispatch"],
)


@router.post("/{location_id}/{parameter_code}")
def trigger_alert_dispatch(
    location_id: int,
    parameter_code: str,
    db: Session = Depends(get_db),
):
    return execute_alert_dispatch(
        db=db,
        location_id=location_id,
        parameter_code=parameter_code,
    )