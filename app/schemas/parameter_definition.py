from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ParameterDefinitionResponse(BaseModel):
    id: int
    parameter_code: str
    display_name: str
    category: Optional[str] = None
    expected_unit: Optional[str] = None
    description: Optional[str] = None
    threshold_profile: Optional[str] = None
    regulatory_source: Optional[str] = None
    warn_min: Optional[float] = None
    warn_max: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    alerts_enabled: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True