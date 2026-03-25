from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.normalized_water_record import NormalizedWaterRecord

router = APIRouter(prefix="/normalized-records", tags=["Normalized Records"])


@router.get("")
def list_normalized_records(db: Session = Depends(get_db)):
    records = (
        db.query(NormalizedWaterRecord)
        .order_by(NormalizedWaterRecord.id.desc())
        .limit(200)
        .all()
    )

    return [
        {
            "id": r.id,
            "raw_record_id": r.raw_record_id,
            "source_id": r.source_id,
            "ingestion_run_id": r.ingestion_run_id,
            "location_name": r.location_name,
            "parameter_code": r.parameter_code,
            "parameter_name": r.parameter_name,
            "measured_value": r.measured_value,
            "unit": r.unit,
            "original_value": r.original_value,
            "original_unit": r.original_unit,
            "threshold": r.threshold,
            "status": r.status,
            "sample_date": r.sample_date,
            "created_at": r.created_at,
        }
        for r in records
    ]