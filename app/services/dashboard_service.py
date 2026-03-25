from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.measurement import Measurement


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _risk_trend_label(db: Session) -> str:
    """
    Simple first-pass trend estimate from alert volume over time.
    """
    now = utc_now()
    last_24h = now - timedelta(hours=24)
    prev_24h = now - timedelta(hours=48)

    recent_count = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.created_at >= last_24h)
    ) or 0

    previous_count = db.scalar(
        select(func.count()).select_from(Alert)
        .where(Alert.created_at >= prev_24h)
        .where(Alert.created_at < last_24h)
    ) or 0

    if recent_count > previous_count:
        return "worsening"
    if recent_count < previous_count:
        return "improving"
    return "stable"


def _top_risk_level(db: Session) -> str:
    critical = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.tier == "CRITICAL")
    ) or 0
    action = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.tier == "ACTION")
    ) or 0
    notice = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.tier == "NOTICE")
    ) or 0

    if critical > 0:
        return "critical"
    if action > 0:
        return "monitoring"
    if notice > 0:
        return "monitoring"
    return "safe"


def _model_confidence(db: Session) -> dict[str, Any]:
    """
    First-pass confidence estimate based on most recent severe alert.
    """
    stmt = (
        select(Alert)
        .where(Alert.tier.in_(["CRITICAL", "ACTION", "NOTICE"]))
        .order_by(Alert.last_seen_at.desc(), Alert.id.desc())
        .limit(1)
    )
    alert = db.execute(stmt).scalars().first()

    if not alert:
        return {
            "confidence_score": 0,
            "confidence_label": "no active risk model output",
        }

    confidence = (getattr(alert, "confidence", "suspected") or "suspected").lower()

    if confidence == "confirmed":
        return {"confidence_score": 88, "confidence_label": "high confidence"}
    if confidence == "suspected":
        return {"confidence_score": 68, "confidence_label": "moderate confidence"}

    return {"confidence_score": 50, "confidence_label": "preliminary confidence"}


def _recommended_actions(db: Session) -> list[str]:
    stmt = (
        select(Alert)
        .where(Alert.tier.in_(["CRITICAL", "ACTION", "NOTICE"]))
        .order_by(Alert.last_seen_at.desc(), Alert.id.desc())
        .limit(1)
    )
    alert = db.execute(stmt).scalars().first()

    if not alert:
        return ["Continue routine monitoring."]

    tier = (getattr(alert, "tier", "NOTICE") or "NOTICE").upper()

    if tier == "CRITICAL":
        return [
            "Restrict drinking and cooking use until confirmatory review is completed.",
            "Inspect the likely source zone immediately.",
            "Notify affected stakeholders and review recent measurements.",
        ]
    if tier == "ACTION":
        return [
            "Review recent measurements and inspect local infrastructure.",
            "Increase sampling frequency in the affected zone.",
            "Notify responsible site personnel for follow-up.",
        ]

    return [
        "Continue monitoring the affected location.",
        "Review trend movement and watch for repeat occurrences.",
    ]


def _water_use_guidance(db: Session) -> list[dict[str, str]]:
    stmt = (
        select(Alert)
        .where(Alert.tier.in_(["CRITICAL", "ACTION", "NOTICE"]))
        .order_by(Alert.last_seen_at.desc(), Alert.id.desc())
        .limit(1)
    )
    alert = db.execute(stmt).scalars().first()

    if not alert:
        safe_activities = [
            "drinking",
            "cooking",
            "brushing_teeth",
            "bathing",
            "laundry",
            "cleaning",
            "toilet",
        ]
        return [{"activity": a, "status": "safe", "label": "Safe"} for a in safe_activities]

    tier = (getattr(alert, "tier", "NOTICE") or "NOTICE").upper()

    if tier == "CRITICAL":
        return [
            {"activity": "drinking", "status": "avoid", "label": "Avoid"},
            {"activity": "cooking", "status": "avoid", "label": "Avoid"},
            {"activity": "brushing_teeth", "status": "avoid", "label": "Avoid"},
            {"activity": "bathing", "status": "caution", "label": "Use caution"},
            {"activity": "laundry", "status": "safe", "label": "Safe"},
            {"activity": "cleaning", "status": "safe", "label": "Safe"},
            {"activity": "toilet", "status": "safe", "label": "Safe"},
        ]

    if tier == "ACTION":
        return [
            {"activity": "drinking", "status": "caution", "label": "Use caution"},
            {"activity": "cooking", "status": "caution", "label": "Use caution"},
            {"activity": "brushing_teeth", "status": "caution", "label": "Use caution"},
            {"activity": "bathing", "status": "safe", "label": "Safe"},
            {"activity": "laundry", "status": "safe", "label": "Safe"},
            {"activity": "cleaning", "status": "safe", "label": "Safe"},
            {"activity": "toilet", "status": "safe", "label": "Safe"},
        ]

    return [
        {"activity": "drinking", "status": "safe", "label": "Safe"},
        {"activity": "cooking", "status": "safe", "label": "Safe"},
        {"activity": "brushing_teeth", "status": "safe", "label": "Safe"},
        {"activity": "bathing", "status": "safe", "label": "Safe"},
        {"activity": "laundry", "status": "safe", "label": "Safe"},
        {"activity": "cleaning", "status": "safe", "label": "Safe"},
        {"activity": "toilet", "status": "safe", "label": "Safe"},
    ]


def get_dashboard_overview(db: Session) -> dict[str, Any]:
    total_alerts = db.scalar(select(func.count()).select_from(Alert)) or 0
    total_measurements = db.scalar(select(func.count()).select_from(Measurement)) or 0

    active_alerts = db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status.in_(["queued", "sending", "failed"]))
    ) or 0

    latest_alert = db.execute(
        select(Alert).order_by(Alert.last_seen_at.desc(), Alert.id.desc()).limit(1)
    ).scalars().first()

    risk_level = _top_risk_level(db)
    confidence_data = _model_confidence(db)

    return {
        "risk_level": risk_level,
        "confidence_score": confidence_data["confidence_score"],
        "confidence_label": confidence_data["confidence_label"],
        "risk_trend": _risk_trend_label(db),
        "last_updated": _safe_iso(getattr(latest_alert, "last_seen_at", None)),
        "signals_refreshed_at": _safe_iso(getattr(latest_alert, "last_seen_at", None)),
        "recommended_actions": _recommended_actions(db),
        "total_parameters": 136,
        "total_measurements": total_measurements,
        "total_alerts": total_alerts,
        "status_summary": {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "critical_count": db.scalar(
                select(func.count()).select_from(Alert).where(Alert.tier == "CRITICAL")
            ) or 0,
            "action_count": db.scalar(
                select(func.count()).select_from(Alert).where(Alert.tier == "ACTION")
            ) or 0,
            "notice_count": db.scalar(
                select(func.count()).select_from(Alert).where(Alert.tier == "NOTICE")
            ) or 0,
        },
        "tap_zone_profile": {
            "location_label": getattr(latest_alert, "location_label", None),
            "county_code": getattr(latest_alert, "county_code", None),
            "cluster_code": getattr(latest_alert, "cluster_code", None),
            "state_region": getattr(latest_alert, "state_region", None),
            "country": getattr(latest_alert, "country", None),
        },
        "water_use_guidance": _water_use_guidance(db),
    }


def get_dashboard_risk_summary(db: Session) -> dict[str, Any]:
    alerts = db.execute(select(Alert)).scalars().all()

    total_alerts = len(alerts)
    action_alerts = sum(
        1 for alert in alerts if str(getattr(alert, "tier", "")).upper() == "ACTION"
    )
    critical_alerts = sum(
        1 for alert in alerts if str(getattr(alert, "tier", "")).upper() == "CRITICAL"
    )

    parameter_counter = Counter(
        alert.parameter_code
        for alert in alerts
        if getattr(alert, "parameter_code", None)
    )

    hotspot_counter = Counter(
        (alert.scope_type, alert.scope_id)
        for alert in alerts
        if getattr(alert, "scope_type", None) is not None
    )

    top_risky_parameters = [
        {"parameter_code": parameter_code, "count": count}
        for parameter_code, count in parameter_counter.most_common(5)
    ]

    hotspot_scopes = [
        {"scope_type": scope_type, "scope_id": scope_id, "count": count}
        for (scope_type, scope_id), count in hotspot_counter.most_common(5)
    ]

    return {
        "total_alerts": total_alerts,
        "action_alerts": action_alerts,
        "critical_alerts": critical_alerts,
        "top_risky_parameters": top_risky_parameters,
        "hotspot_scopes": hotspot_scopes,
    }