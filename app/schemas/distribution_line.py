from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DistributionLineCreate(BaseModel):
    central_system_id: int
    line_code: str
    line_name: str
    region: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    is_active: bool = True


class DistributionLineRead(BaseModel):
    id: int
    central_system_id: int
    line_code: str
    line_name: str
    region: Optional[str]
    state: Optional[str]
    county: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True