from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.measurement import Measurement
from app.models.normalized_water_record import NormalizedWaterRecord
from app.models.water_sample import WaterSample
from app.services.measurement_evaluator import evaluate_measurement


def parse_sample_datetime(sample_date: str | None) -> datetime:
    if not sample_date:
        return datetime.now(timezone.utc)

    try:
        return datetime.fromisoformat(sample_date).astimezone(timezone.utc)
    except Exception:
        try:
            return datetime.strptime(sample_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)


def get_or_create_water_sample(
    db: Session,
    *,
    location_id: int,
    collected_at: datetime,
    method: str,
    notes: str | None = None,
) -> WaterSample:
    existing = (
        db.query(WaterSample)
        .filter(
            WaterSample.location_id == location_id,
            WaterSample.collected_at == collected_at,
            WaterSample.method == method,
        )
        .first()
    )

    if existing:
        return existing

    sample = WaterSample(
        location_id=location_id,
        collected_at=collected_at,
        method=method,
        notes=notes,
    )
    db.add(sample)
    db.flush()
    return sample


def measurement_exists(
    db: Session,
    *,
    sample_id: int,
    parameter_code: str,
    value: float,
) -> bool:
    existing = (
        db.query(Measurement)
        .filter(
            Measurement.sample_id == sample_id,
            Measurement.parameter_code == parameter_code,
            Measurement.value == value,
        )
        .first()
    )
    return existing is not None


def build_sample_parameters(
    db: Session,
    *,
    sample_id: int,
) -> dict[str, float]:
    measurements = (
        db.query(Measurement)
        .filter(Measurement.sample_id == sample_id)
        .all()
    )

    parameters: dict[str, float] = {}
    for measurement in measurements:
        if measurement.parameter_code and measurement.value is not None:
            parameters[measurement.parameter_code] = measurement.value

    return parameters


def resolve_alert_user_id(source: DataSource) -> int | None:
    return getattr(source, "created_by_user_id", None)


def persist_normalized_records_to_measurements(
    db: Session,
    *,
    source: DataSource,
    normalized_records: list[NormalizedWaterRecord],
) -> int:
    if not source.default_location_id:
        raise ValueError(
            "Data source has no default_location_id. Assign a location before pushing normalized records."
        )

    created_count = 0
    alert_user_id = resolve_alert_user_id(source)

    for record in normalized_records:
        collected_at = parse_sample_datetime(record.sample_date)

        sample = get_or_create_water_sample(
            db,
            location_id=source.default_location_id,
            collected_at=collected_at,
            method="institution_upload",
            notes=f"Created from source_id={source.id}, ingestion_run_id={record.ingestion_run_id}",
        )

        if measurement_exists(
            db,
            sample_id=sample.id,
            parameter_code=record.parameter_code,
            value=record.measured_value,
        ):
            continue

        evaluation_status = evaluate_measurement(
            db=db,
            parameter_code=record.parameter_code,
            value=record.measured_value,
            unit=record.unit,
        )

        measurement = Measurement(
            sample_id=sample.id,
            parameter_code=record.parameter_code,
            value=record.measured_value,
            unit=record.unit,
            qualifier=None,
            method="institution_upload_normalized",
            measured_at=collected_at,
            source_type="institution_upload",
            quality_flag=evaluation_status,
        )
        db.add(measurement)
        db.flush()

        created_count += 1

        sample_parameters = build_sample_parameters(
            db,
            sample_id=sample.id,
        )

        if evaluation_status in {"attention", "critical"} and alert_user_id is not None:
            from app.services.measurement_alert_service import create_alert_from_measurement

            create_alert_from_measurement(
                db=db,
                user_id=alert_user_id,
                scope_type="location",
                scope_id=source.default_location_id,
                parameters=sample_parameters,
                measurement_id=measurement.id,
                source_kind="site",
            )

    db.flush()
    return created_count