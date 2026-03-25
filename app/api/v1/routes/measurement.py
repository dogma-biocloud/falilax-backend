from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.measurement import Measurement
from app.schemas.measurement import MeasurementCreate, MeasurementResponse
from app.services.measurement_service import (
    get_all_measurements,
    create_measurement,
)

router = APIRouter()


@router.get("/measurements", response_model=List[MeasurementResponse])
def list_measurements(
    sample_id: int | None = None,
    parameter_code: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List measurements, optionally filtered.
    """
    query = db.query(Measurement)

    if sample_id is not None:
        query = query.filter(Measurement.sample_id == sample_id)

    if parameter_code:
        query = query.filter(Measurement.parameter_code == parameter_code)

    return query.order_by(desc(Measurement.id)).limit(limit).all()


@router.post("/measurements", response_model=MeasurementResponse, status_code=201)
def create_new_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
):
    return create_measurement(db, payload)


@router.get("/measurements/latest")
def latest_measurements(
    sample_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Returns the most recent measurement per parameter_code.
    Useful for frontend signal cards.
    """
    query = db.query(Measurement)

    if sample_id is not None:
        query = query.filter(Measurement.sample_id == sample_id)

    rows = query.order_by(desc(Measurement.id)).all()

    seen: set[str] = set()
    latest: list[dict] = []

    for m in rows:
        code = getattr(m, "parameter_code", None)
        if not code or code in seen:
            continue
        seen.add(code)

        latest.append(
            {
                "id": m.id,
                "sample_id": m.sample_id,
                "parameter_code": m.parameter_code,
                "value": m.value,
                "unit": m.unit,
            }
        )

    return latest


@router.get("/measurements/timeseries")
def measurement_timeseries(
    parameter_code: str,
    sample_id: int | None = None,
    limit: int = Query(default=30, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """
    Returns ordered timeseries data for one parameter.
    Useful for sparkline charts / trend graphs.
    """
    query = db.query(Measurement).filter(Measurement.parameter_code == parameter_code)

    if sample_id is not None:
        query = query.filter(Measurement.sample_id == sample_id)

    rows = (
        query.order_by(Measurement.id.asc())
        .limit(limit)
        .all()
    )

    return {
        "parameter_code": parameter_code,
        "sample_id": sample_id,
        "points": [
            {
                "id": m.id,
                "value": m.value,
                "unit": m.unit,
            }
            for m in rows
        ],
    }