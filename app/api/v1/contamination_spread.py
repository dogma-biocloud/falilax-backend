from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.contamination_spread_service import analyze_contamination_spread

router = APIRouter(prefix="/contamination-spread", tags=["Contamination Spread"])


@router.get("/{parameter_code}")
def get_contamination_spread(
    parameter_code: str,
    db: Session = Depends(get_db),
):
    return analyze_contamination_spread(
        db=db,
        parameter_code=parameter_code,
    )