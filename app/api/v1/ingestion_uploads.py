from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.raw_water_record import RawWaterRecord
from app.schemas.ingestion import FileIngestionResponse
from app.services.file_ingestion_service import parse_csv_bytes, parse_xlsx_bytes

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/upload/{source_id}", response_model=FileIngestionResponse)
async def upload_source_file(
    source_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    filename = file.filename or "uploaded_file"
    suffix = Path(filename).suffix.lower()

    if suffix not in [".csv", ".xlsx"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only .csv and .xlsx are accepted.",
        )

    ingestion_run = IngestionRun(
        source_id=source_id,
        status="started",
        records_extracted=0,
        records_loaded=0,
    )
    db.add(ingestion_run)
    db.commit()
    db.refresh(ingestion_run)

    try:
        file_bytes = await file.read()

        if suffix == ".csv":
            rows = parse_csv_bytes(file_bytes)
        else:
            rows = parse_xlsx_bytes(file_bytes)

        records_extracted = len(rows)
        records_loaded = 0

        for idx, row in enumerate(rows):
            raw_record = RawWaterRecord(
                source_id=source_id,
                ingestion_run_id=ingestion_run.id,
                source_record_id=str(idx + 1),
                raw_payload=row,
                processing_status="pending",
            )
            db.add(raw_record)
            records_loaded += 1

        ingestion_run.status = "success"
        ingestion_run.records_extracted = records_extracted
        ingestion_run.records_loaded = records_loaded
        ingestion_run.finished_at = datetime.now(timezone.utc)
        ingestion_run.log_summary = f"Processed file {filename}"

        db.commit()
        db.refresh(ingestion_run)

        return FileIngestionResponse(
            message="File ingested successfully",
            source_id=source_id,
            ingestion_run_id=ingestion_run.id,
            filename=filename,
            records_extracted=records_extracted,
            records_loaded=records_loaded,
            status=ingestion_run.status,
        )

    except Exception as exc:
        ingestion_run.status = "failed"
        ingestion_run.finished_at = datetime.now(timezone.utc)
        ingestion_run.error_message = str(exc)
        db.commit()

        raise HTTPException(status_code=500, detail=f"File ingestion failed: {exc}")