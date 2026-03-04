from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.water_sample import WaterSampleResponse, WaterSampleCreate
from app.services.water_sample_service import get_all_water_samples, create_water_sample

router = APIRouter()


@router.get("/water-samples", response_model=List[WaterSampleResponse])
def list_water_samples(db: Session = Depends(get_db)):
    return get_all_water_samples(db)


@router.post("/water-samples", response_model=WaterSampleResponse, status_code=201)
def create_new_water_sample(payload: WaterSampleCreate, db: Session = Depends(get_db)):
    return create_water_sample(db, payload)