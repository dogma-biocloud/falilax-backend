from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["alert-timeline"])


@router.get("/timeline")
def alerts_timeline(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Returns daily alert counts grouped by tier for charting.

    Example output:
    [
      {"date": "2026-03-01", "critical": 2, "action": 4, "notice": 1},
      {"date": "2026-03-02", "critical": 1, "action": 3, "notice": 5}
    ]
    """

    # PostgreSQL-friendly date grouping
    day_bucket = func.date(Alert.created_at)

    stmt = (
        select(
            day_bucket.label("day"),
            Alert.tier,
            func.count(Alert.id).label("count"),
        )
        .group_by(day_bucket, Alert.tier)
        .order_by(day_bucket.asc())
    )

    rows = db.execute(stmt).all()

    timeline_map: dict[str, dict] = {}

    for day, tier, count in rows:
        day_str = str(day)

        if day_str not in timeline_map:
            timeline_map[day_str] = {
                "date": day_str,
                "critical": 0,
                "action": 0,
                "notice": 0,
            }

        normalized_tier = (tier or "").upper()

        if normalized_tier == "CRITICAL":
            timeline_map[day_str]["critical"] = count
        elif normalized_tier == "ACTION":
            timeline_map[day_str]["action"] = count
        elif normalized_tier == "NOTICE":
            timeline_map[day_str]["notice"] = count

    # keep only the most recent requested number of days
    results = list(timeline_map.values())
    return results[-days:]