# app/services/measurement_pipeline.py
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.measurement import Measurement
from app.services.alert_engine import process_measurement_for_alerts


def create_measurement_and_alerts(
    db: Session,
    *,
    user_id: int,
    sample_id: int,
    parameter_code: str,
    value: float,
    unit: Optional[str] = None,
    # geo routing tags (hierarchy)
    cluster_code: Optional[str] = None,
    region_code: Optional[str] = None,
    county_code: Optional[str] = None,
    state_region: Optional[str] = None,
    country: Optional[str] = None,
    # third layer: specific place (household/school/restaurant/etc)
    location_label: Optional[str] = None,   # e.g., "Apt F", "Sunyani SHS Lab", "Restaurant - Kitchen Tap"
    address_line1: Optional[str] = None,
    address_line2: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    plus_code: Optional[str] = None,
    landmark: Optional[str] = None,
    directions_hint: Optional[str] = None,
    # attribution (optional)
    origin_scope_type: str = "unknown",
    origin_scope_id: Optional[int] = None,
) -> Measurement:
    """
    1) Insert Measurement
    2) Commit so it has an id + is durable
    3) Run alert engine for that measurement (creates queued alerts if threshold breached)
    """

    m = Measurement(
        sample_id=sample_id,
        parameter_code=parameter_code,
        value=value,
        unit=unit,
    )

    # Only set user_id if your Measurement model actually has it
    if hasattr(Measurement, "user_id"):
        setattr(m, "user_id", user_id)

    db.add(m)
    db.commit()
    db.refresh(m)

    process_measurement_for_alerts(
        db,
        user_id=user_id,
        sample_id=sample_id,
        parameter_code=parameter_code,
        value=float(value),
        unit=unit,
        # attribution
        origin_scope_type=origin_scope_type,
        origin_scope_id=origin_scope_id,
        # geo
        cluster_code=cluster_code,
        region_code=region_code,
        county_code=county_code,
        state_region=state_region,
        country=country,
        # delivery (keep simple for now)
        delivery_channel="in_app",
        recipient=None,
        scheduled_for=None,
        # specific place context
        location_label=location_label,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        postal_code=postal_code,
        latitude=latitude,
        longitude=longitude,
        plus_code=plus_code,
        landmark=landmark,
        directions_hint=directions_hint,
    )

    return m