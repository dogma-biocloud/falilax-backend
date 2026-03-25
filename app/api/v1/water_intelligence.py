from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.water_intelligence_service import (
    build_water_intelligence_snapshot,
)

router = APIRouter(
    prefix="/water-intelligence",
    tags=["Water Intelligence"],
)


@router.get("/{location_id}/{parameter_code}")
def get_water_intelligence(
    location_id: int,
    parameter_code: str,
    db: Session = Depends(get_db),
):
    return build_water_intelligence_snapshot(
        db=db,
        location_id=location_id,
        parameter_code=parameter_code,
    )