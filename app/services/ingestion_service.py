from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.normalized_water_record import NormalizedWaterRecord
from app.models.raw_water_record import RawWaterRecord
from app.services.normalization_service import normalize_raw_row


def start_ingestion_run(
    db: Session,
    *,
    source_id: int,
) -> IngestionRun:
    run = IngestionRun(
        source_id=source_id,
        status="started",
        records_extracted=0,
        records_loaded=0,
    )
    db.add(run)
    db.flush()
    return run


def ingest_rows_for_source(
    db: Session,
    *,
    source: DataSource,
    rows: list[dict],
) -> IngestionRun:
    run = start_ingestion_run(db, source_id=source.id)

    extracted_count = 0
    loaded_count = 0

    for row in rows:
        extracted_count += 1

        raw_record = RawWaterRecord(
            source_id=source.id,
            ingestion_run_id=run.id,
            external_record_id=None,
            payload=row,
            parsing_status="parsed",
            error_message=None,
        )
        db.add(raw_record)
        db.flush()

        normalized_records = normalize_raw_row(
            raw_row=row,
            parser_type=source.parser_type,
        )

        for record in normalized_records:
            normalized = NormalizedWaterRecord(
                raw_record_id=raw_record.id,
                source_id=source.id,
                ingestion_run_id=run.id,
                location_name=record["location_name"],
                parameter_code=record["parameter_code"],
                parameter_name=record["parameter_name"],
                measured_value=record["measured_value"],
                unit=record["unit"],
                original_value=record.get("original_value"),
                original_unit=record.get("original_unit"),
                threshold=record.get("threshold"),
                status=record["status"],
                sample_date=record.get("sample_date"),
                notes=None,
            )
            db.add(normalized)
            loaded_count += 1

    run.records_extracted = extracted_count
    run.records_loaded = loaded_count
    run.status = "success"

    db.flush()
    return run