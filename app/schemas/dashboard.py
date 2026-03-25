from typing import List
from pydantic import BaseModel


class AlertTierCount(BaseModel):
    tier: str
    count: int


class LatestMeasurementItem(BaseModel):
    parameter_code: str
    value: float
    unit: str | None = None
    quality_flag: str | None = None
    source_type: str | None = None


class TopAlertParameterItem(BaseModel):
    parameter_code: str
    count: int


class DashboardOverviewResponse(BaseModel):
    total_parameters: int
    total_measurements: int
    total_alerts: int
    alert_tiers: List[AlertTierCount]
    latest_measurements: List[LatestMeasurementItem]
    top_alert_parameters: List[TopAlertParameterItem]
class HotspotScopeItem(BaseModel):
    scope_type: str
    scope_id: int | None = None
    count: int


class RiskSummaryResponse(BaseModel):
    total_alerts: int
    action_alerts: int
    critical_alerts: int
    top_risky_parameters: List[TopAlertParameterItem]
    hotspot_scopes: List[HotspotScopeItem]