from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.alert_ingest import AlertIngestRequest, AlertIngestResponse
from app.services.measurement_pipeline import create_measurement_and_alerts

router = APIRouter(prefix="/alerts", tags=["alert-ingestion"])


@router.post("/ingest", response_model=AlertIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_alert_reading(
    payload: AlertIngestRequest,
    db: Session = Depends(get_db),
) -> AlertIngestResponse:
    measurement = create_measurement_and_alerts(
        db,
        user_id=payload.user_id,
        sample_id=payload.sample_id,
        parameter_code=payload.parameter_code,
        value=payload.value,
        unit=payload.unit,
        cluster_code=payload.cluster_code,
        region_code=payload.region_code,
        county_code=payload.county_code,
        state_region=payload.state_region,
        country=payload.country,
        location_label=payload.location_label,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        postal_code=payload.postal_code,
        plus_code=payload.plus_code,
        landmark=payload.landmark,
        directions_hint=payload.directions_hint,
        origin_scope_type=payload.origin_scope_type,
        origin_scope_id=payload.origin_scope_id,
    )

    return AlertIngestResponse(
        message="Reading ingested successfully",
        measurement_id=measurement.id,
    )