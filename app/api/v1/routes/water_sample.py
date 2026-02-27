from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.water_sample import WaterSample
from app.schemas.water_sample import WaterSampleResponse  # ✅ import schema

router = APIRouter()

@router.get("/water-samples", response_model=list[WaterSampleResponse])
def list_water_samples(db: Session = Depends(get_db)):
    samples = db.query(WaterSample).all()
    return samples