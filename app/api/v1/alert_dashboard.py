from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/alerts/dashboard", tags=["alert-dashboard"])


@router.get("/summary")
def alert_summary(db: Session = Depends(get_db)) -> dict:
    total_alerts = db.scalar(select(func.count()).select_from(Alert)) or 0
    queued = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == "queued")
    ) or 0
    sending = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == "sending")
    ) or 0
    sent = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == "sent")
    ) or 0
    failed = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == "failed")
    ) or 0

    critical = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.tier == "CRITICAL")
    ) or 0
    action = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.tier == "ACTION")
    ) or 0
    notice = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.tier == "NOTICE")
    ) or 0

    return {
        "total_alerts": total_alerts,
        "by_status": {
            "queued": queued,
            "sending": sending,
            "sent": sent,
            "failed": failed,
        },
        "by_tier": {
            "critical": critical,
            "action": action,
            "notice": notice,
        },
    }


@router.get("/by-tier")
def alerts_by_tier(db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(Alert.tier, func.count(Alert.id).label("count"))
        .group_by(Alert.tier)
        .order_by(Alert.tier.asc())
    )
    rows = db.execute(stmt).all()

    return [{"tier": tier, "count": count} for tier, count in rows]


@router.get("/by-county")
def alerts_by_county(db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(Alert.county_code, func.count(Alert.id).label("count"))
        .group_by(Alert.county_code)
        .order_by(desc(func.count(Alert.id)))
    )
    rows = db.execute(stmt).all()

    return [
        {"county_code": county_code or "UNKNOWN", "count": count}
        for county_code, count in rows
    ]


@router.get("/by-parameter")
def alerts_by_parameter(db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(Alert.parameter_code, func.count(Alert.id).label("count"))
        .group_by(Alert.parameter_code)
        .order_by(desc(func.count(Alert.id)))
    )
    rows = db.execute(stmt).all()

    return [
        {"parameter_code": parameter_code or "unknown", "count": count}
        for parameter_code, count in rows
    ]


@router.get("/recent")
def recent_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Alert)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
    )
    alerts = db.execute(stmt).scalars().all()

    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "tier": a.tier,
            "status": a.status,
            "parameter_code": a.parameter_code,
            "title": a.title,
            "message": a.message,
            "occurrence_count": a.occurrence_count,
            "scope_type": a.scope_type,
            "scope_id": a.scope_id,
            "cluster_code": a.cluster_code,
            "region_code": a.region_code,
            "county_code": a.county_code,
            "state_region": a.state_region,
            "country": a.country,
            "location_label": a.location_label,
            "delivery_channel": a.delivery_channel,
            "recipient": a.recipient,
            "created_at": a.created_at,
            "sent_at": a.sent_at,
            "last_error": a.last_error,
        }
        for a in alerts
    ]