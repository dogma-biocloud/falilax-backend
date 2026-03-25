from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_service import (
    get_dashboard_overview,
    get_dashboard_risk_summary,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db)) -> dict:
    """
    High-level dashboard metrics and model insight.
    """
    return get_dashboard_overview(db)


@router.get("/risk-summary")
def dashboard_risk_summary(db: Session = Depends(get_db)) -> dict:
    """
    Summary of active alerts and high-risk parameters for dashboard widgets.
    """
    return get_dashboard_risk_summary(db)