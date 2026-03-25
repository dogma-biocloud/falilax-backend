from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.normalized_water_record import NormalizedWaterRecord
from app.models.raw_water_record import RawWaterRecord
from app.schemas.normalization import NormalizationResponse
from app.services.normalization_service import normalize_raw_row

router = APIRouter(prefix="/normalization", tags=["Normalization"])


@router.post("/run/{ingestion_run_id}", response_model=NormalizationResponse)
def run_normalization(ingestion_run_id: int, db: Session = Depends(get_db)):
    ingestion_run = (
        db.query(IngestionRun)
        .filter(IngestionRun.id == ingestion_run_id)
        .first()
    )
    if not ingestion_run:
        raise HTTPException(status_code=404, detail="Ingestion run not found")

    source = db.query(DataSource).filter(DataSource.id == ingestion_run.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    raw_records = (
        db.query(RawWaterRecord)
        .filter(RawWaterRecord.ingestion_run_id == ingestion_run_id)
        .all()
    )
    if not raw_records:
        raise HTTPException(status_code=404, detail="No raw records found for ingestion run")

    raw_records_seen = len(raw_records)
    normalized_records_created = 0

    for raw_record in raw_records:
        payload = raw_record.raw_payload or {}
        normalized = normalize_raw_row(payload, parser_type=source.parser_type)

        if normalized:
            for item in normalized:
                normalized_record = NormalizedWaterRecord(
                    raw_record_id=raw_record.id,
                    source_id=raw_record.source_id,
                    ingestion_run_id=raw_record.ingestion_run_id,
                    location_name=item["location_name"],
                    parameter_code=item["parameter_code"],
                    parameter_name=item["parameter_name"],
                    measured_value=item["measured_value"],
                    unit=item["unit"],
                    original_value=item["original_value"],
                    original_unit=item["original_unit"],
                    threshold=item["threshold"],
                    status=item["status"],
                    sample_date=item["sample_date"],
                )
                db.add(normalized_record)
                normalized_records_created += 1

            raw_record.processing_status = "normalized"
            raw_record.error_message = None
        else:
            raw_record.processing_status = "failed"
            raw_record.error_message = "No recognized parameter fields found"

    db.commit()

    return NormalizationResponse(
        ingestion_run_id=ingestion_run_id,
        raw_records_seen=raw_records_seen,
        normalized_records_created=normalized_records_created,
        message="Normalization completed",
    )