from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.measurement import MeasurementCreate, MeasurementResponse
from app.services.measurement_service import (
    get_all_measurements,
    create_measurement,
)

router = APIRouter()


@router.get("/measurements", response_model=List[MeasurementResponse])
def list_measurements(db: Session = Depends(get_db)):
    return get_all_measurements(db)


@router.post("/measurements", response_model=MeasurementResponse, status_code=201)
def create_new_measurement(payload: MeasurementCreate, db: Session = Depends(get_db)):
    return create_measurement(db, payload)