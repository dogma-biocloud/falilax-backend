from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/system", tags=["system-status"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    latest_alert = db.execute(
        select(Alert).order_by(Alert.last_seen_at.desc(), Alert.id.desc()).limit(1)
    ).scalars().first()

    now = utc_now()
    refreshed_at = getattr(latest_alert, "last_seen_at", None)
    next_update = now + timedelta(minutes=15)

    if refreshed_at is None:
        health = "idle"
    else:
        delta = now - refreshed_at
        if delta <= timedelta(minutes=15):
            health = "healthy"
        elif delta <= timedelta(hours=1):
            health = "degraded"
        else:
            health = "stale"

    return {
        "signals_refreshed_at": refreshed_at.isoformat() if refreshed_at else None,
        "next_model_update": next_update.isoformat(),
        "system_health": health,
    }