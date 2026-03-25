from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["alert-map"])


@router.get("/map")
def alerts_map(db: Session = Depends(get_db)) -> dict:
    alerts = db.execute(
        select(Alert)
        .where(Alert.latitude.is_not(None))
        .where(Alert.longitude.is_not(None))
        .order_by(desc(Alert.last_seen_at), desc(Alert.id))
        .limit(200)
    ).scalars().all()

    districts_monitored = db.scalar(
        select(func.count(func.distinct(Alert.county_code))).where(Alert.county_code.is_not(None))
    ) or 0

    total_facilities = db.scalar(
        select(func.count(func.distinct(Alert.location_label))).where(Alert.location_label.is_not(None))
    ) or 0

    active_alerts = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status.in_(["queued", "sending", "failed"]))
    ) or 0

    by_county = db.execute(
        select(Alert.county_code, func.count(Alert.id).label("count"))
        .group_by(Alert.county_code)
        .order_by(desc(func.count(Alert.id)))
    ).all()

    markers = [
        {
            "id": a.id,
            "location_label": a.location_label,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "status": ("critical" if a.tier == "CRITICAL" else "monitor" if a.tier in ("ACTION", "NOTICE") else "safe"),
            "tier": a.tier,
            "parameter_code": a.parameter_code,
            "measured_value": getattr(a, "measured_value", None),
            "unit": getattr(a, "unit", None),
            "last_updated": a.last_seen_at.isoformat() if a.last_seen_at else None,
            "county_code": a.county_code,
            "cluster_code": a.cluster_code,
            "state_region": a.state_region,
            "country": a.country,
            "title": a.title,
        }
        for a in alerts
    ]

    attention_areas = [
        {"county_code": county or "UNKNOWN", "count": count}
        for county, count in by_county[:10]
    ]

    return {
        "summary": {
            "districts_monitored": districts_monitored,
            "total_facilities": total_facilities,
            "coverage_area": "Configured geography",
            "active_alerts": active_alerts,
        },
        "markers": markers,
        "attention_areas": attention_areas,
    }