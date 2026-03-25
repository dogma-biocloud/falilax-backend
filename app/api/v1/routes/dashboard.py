from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert
from app.models.measurement import Measurement
from app.models.parameter_definition import ParameterDefinition
from app.schemas.dashboard import (
    AlertTierCount,
    DashboardOverviewResponse,
    HotspotScopeItem,
    LatestMeasurementItem,
    RiskSummaryResponse,
    TopAlertParameterItem,
)

router = APIRouter()


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(db: Session = Depends(get_db)):
    total_parameters = db.query(ParameterDefinition).count()
    total_measurements = db.query(Measurement).count()
    total_alerts = db.query(Alert).count()

    alert_rows = db.query(Alert).all()
    tier_counter = Counter((a.tier or "UNKNOWN") for a in alert_rows)
    alert_tiers = [
        AlertTierCount(tier=tier, count=count)
        for tier, count in sorted(tier_counter.items())
    ]

    latest_rows = (
        db.query(Measurement)
        .order_by(Measurement.id.desc())
        .limit(10)
        .all()
    )
    latest_measurements = [
        LatestMeasurementItem(
            parameter_code=m.parameter_code,
            value=m.value,
            unit=m.unit,
            quality_flag=getattr(m, "quality_flag", None),
            source_type=getattr(m, "source_type", None),
        )
        for m in latest_rows
    ]

    parameter_counter = Counter(
        a.parameter_code for a in alert_rows if a.parameter_code
    )
    top_alert_parameters = [
        TopAlertParameterItem(parameter_code=code, count=count)
        for code, count in parameter_counter.most_common(10)
    ]

    return DashboardOverviewResponse(
        total_parameters=total_parameters,
        total_measurements=total_measurements,
        total_alerts=total_alerts,
        alert_tiers=alert_tiers,
        latest_measurements=latest_measurements,
        top_alert_parameters=top_alert_parameters,
    )


@router.get("/dashboard/risk-summary", response_model=RiskSummaryResponse)
def dashboard_risk_summary(db: Session = Depends(get_db)):
    alert_rows = db.query(Alert).all()

    total_alerts = len(alert_rows)
    action_alerts = sum(1 for a in alert_rows if (a.tier or "").upper() == "ACTION")
    critical_alerts = sum(1 for a in alert_rows if (a.tier or "").upper() == "CRITICAL")

    parameter_counter = Counter(
        a.parameter_code for a in alert_rows if a.parameter_code
    )
    top_risky_parameters = [
        TopAlertParameterItem(parameter_code=code, count=count)
        for code, count in parameter_counter.most_common(10)
    ]

    scope_counter = Counter(
        (a.scope_type or "unknown", a.scope_id) for a in alert_rows
    )
    hotspot_scopes = [
        HotspotScopeItem(scope_type=scope_type, scope_id=scope_id, count=count)
        for (scope_type, scope_id), count in scope_counter.most_common(10)
    ]

    return RiskSummaryResponse(
        total_alerts=total_alerts,
        action_alerts=action_alerts,
        critical_alerts=critical_alerts,
        top_risky_parameters=top_risky_parameters,
        hotspot_scopes=hotspot_scopes,
    )