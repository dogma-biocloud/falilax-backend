from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _serialize_alert(a: Alert) -> dict:
    return {
        "id": a.id,
        "user_id": a.user_id,
        "scope_type": a.scope_type,
        "scope_id": a.scope_id,
        "tier": a.tier,
        "title": a.title,
        "message": a.message,
        "status": a.status,
        "parameter_code": a.parameter_code,
        "occurrence_count": a.occurrence_count,
        "delivery_channel": a.delivery_channel,
        "recipient": a.recipient,
        "origin_scope_type": a.origin_scope_type,
        "origin_scope_id": a.origin_scope_id,
        "cluster_code": a.cluster_code,
        "region_code": a.region_code,
        "county_code": a.county_code,
        "state_region": a.state_region,
        "country": a.country,
        "location_label": a.location_label,
        "address_line1": a.address_line1,
        "address_line2": a.address_line2,
        "city": a.city,
        "postal_code": a.postal_code,
        "latitude": a.latitude,
        "longitude": a.longitude,
        "plus_code": a.plus_code,
        "landmark": a.landmark,
        "directions_hint": a.directions_hint,
        "confidence": a.confidence,
        "disclaimer": a.disclaimer,
        "measured_value": getattr(a, "measured_value", None),
        "unit": getattr(a, "unit", None),
        "threshold": getattr(a, "threshold", None),
        "threshold_kind": getattr(a, "threshold_kind", None),
        "delivery_attempts": getattr(a, "delivery_attempts", None),
        "last_error": getattr(a, "last_error", None),
        "last_error_at": getattr(a, "last_error_at", None).isoformat()
        if getattr(a, "last_error_at", None)
        else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None,
        "sent_at": a.sent_at.isoformat() if a.sent_at else None,
        "scheduled_for": a.scheduled_for.isoformat() if a.scheduled_for else None,
    }


@router.get("/")
def list_alerts(
    cluster_code: str | None = None,
    region_code: str | None = None,
    county_code: str | None = None,
    state_region: str | None = None,
    country: str | None = None,
    location_label: str | None = None,
    status: str | None = None,
    tier: str | None = None,
    parameter_code: str | None = None,
    user_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Alert)

    # geo filters
    if location_label:
        query = query.where(Alert.location_label == location_label)

    if cluster_code:
        query = query.where(Alert.cluster_code == cluster_code)

    if region_code:
        query = query.where(Alert.region_code == region_code)

    if county_code:
        query = query.where(Alert.county_code == county_code)

    if state_region:
        query = query.where(Alert.state_region == state_region)

    if country:
        query = query.where(Alert.country == country)

    # alert filters
    if status:
        query = query.where(Alert.status == status)

    if tier:
        query = query.where(Alert.tier == tier.upper())

    if parameter_code:
        query = query.where(Alert.parameter_code == parameter_code)

    if user_id is not None:
        query = query.where(Alert.user_id == user_id)

    query = query.order_by(desc(Alert.last_seen_at), desc(Alert.id)).limit(limit)

    results = db.execute(query).scalars().all()
    return [_serialize_alert(a) for a in results]


@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
) -> dict:
    alert = db.get(Alert, alert_id)
    if not alert:
        return {"detail": "Alert not found"}

    return _serialize_alert(alert)