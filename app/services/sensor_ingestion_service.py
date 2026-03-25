from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.normalized_water_record import NormalizedWaterRecord
from app.models.raw_water_record import RawWaterRecord
from app.schemas.sensor_ingest import SensorIngestRequest
from app.services.measurement_bridge_service import (
    persist_normalized_records_to_measurements,
)


SENSOR_PARAMETER_UNITS = {
    "ph": "pH",
    "turbidity": "NTU",
    "chlorine": "mg/L",
    "lead": "mg/L",
    "copper": "mg/L",
    "nitrate": "mg/L",
}


def create_ingestion_run(
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


def sensor_payload_to_normalized_records(
    *,
    payload: SensorIngestRequest,
    raw_record_id: int,
    source_id: int,
    ingestion_run_id: int,
) -> list[NormalizedWaterRecord]:
    records: list[NormalizedWaterRecord] = []

    readings_dict = payload.readings.model_dump(exclude_none=True)

    for parameter_code, measured_value in readings_dict.items():
        unit = SENSOR_PARAMETER_UNITS.get(parameter_code)

        record = NormalizedWaterRecord(
            raw_record_id=raw_record_id,
            source_id=source_id,
            ingestion_run_id=ingestion_run_id,
            location_name=payload.location_name,
            parameter_code=parameter_code,
            parameter_name=parameter_code.capitalize(),
            measured_value=float(measured_value),
            unit=unit,
            original_value=float(measured_value),
            original_unit=unit,
            threshold=None,
            status="normalized",
            sample_date=payload.recorded_at.isoformat(),
            notes=payload.notes,
        )
        records.append(record)

    return records


def ingest_sensor_payload(
    db: Session,
    *,
    source: DataSource,
    payload: SensorIngestRequest,
) -> dict:
    if not source.default_location_id:
        raise ValueError("Data source must have default_location_id before sensor ingestion")

    ingestion_run = create_ingestion_run(
        db,
        source_id=source.id,
    )

    raw_record = RawWaterRecord(
        source_id=source.id,
        ingestion_run_id=ingestion_run.id,
        external_record_id=payload.device_id,
        payload=payload.model_dump(mode="json"),
        parsing_status="parsed",
        error_message=None,
    )
    db.add(raw_record)
    db.flush()

    normalized_records = sensor_payload_to_normalized_records(
        payload=payload,
        raw_record_id=raw_record.id,
        source_id=source.id,
        ingestion_run_id=ingestion_run.id,
    )

    for record in normalized_records:
        db.add(record)

    db.flush()

    created_measurements = persist_normalized_records_to_measurements(
        db=db,
        source=source,
        normalized_records=normalized_records,
    )

    ingestion_run.records_extracted = 1
    ingestion_run.records_loaded = len(normalized_records)
    ingestion_run.status = "success"

    db.flush()

    return {
        "ingestion_run_id": ingestion_run.id,
        "raw_record_id": raw_record.id,
        "normalized_records_created": len(normalized_records),
        "measurements_created": created_measurements,
        "status": ingestion_run.status,
    }