from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.water_sample import WaterSampleResponse
from app.services.water_sample_service import get_all_water_samples

router = APIRouter()

@router.get("/water-samples", response_model=List[WaterSampleResponse])
def list_water_samples(db: Session = Depends(get_db)):
    return get_all_water_samples(db)