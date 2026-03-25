from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import DataSource
from app.models.normalized_water_record import NormalizedWaterRecord
from app.services.measurement_bridge_service import (
    persist_normalized_records_to_measurements,
)

router = APIRouter(prefix="/measurement-bridge", tags=["Measurement Bridge"])


@router.post("/push/{ingestion_run_id}")
def push_normalized_to_measurements(
    ingestion_run_id: int,
    db: Session = Depends(get_db),
):
    normalized_records = (
        db.query(NormalizedWaterRecord)
        .filter(NormalizedWaterRecord.ingestion_run_id == ingestion_run_id)
        .all()
    )

    if not normalized_records:
        raise HTTPException(
            status_code=404,
            detail="No normalized records found for ingestion run",
        )

    source_id = normalized_records[0].source_id

    source = (
        db.query(DataSource)
        .filter(DataSource.id == source_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    if not source.default_location_id:
        raise HTTPException(
            status_code=400,
            detail="Data source has no default_location_id configured",
        )

    try:
        created_count = persist_normalized_records_to_measurements(
            db=db,
            source=source,
            normalized_records=normalized_records,
        )
        db.commit()

    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to push normalized records to measurements",
        )

    return {
        "message": "Normalized records pushed to measurements successfully",
        "ingestion_run_id": ingestion_run_id,
        "source_id": source.id,
        "default_location_id": source.default_location_id,
        "measurements_created": created_count,
    }