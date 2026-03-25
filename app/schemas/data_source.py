from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DataSourceCreate(BaseModel):
    source_name: str
    organization_name: str
    source_type: str
    endpoint_url: Optional[str] = None
    auth_type: Optional[str] = None
    parser_type: str = "generic"
    refresh_interval_minutes: Optional[int] = None
    region: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    default_location_id: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None


class DataSourceRead(BaseModel):
    id: int
    source_name: str
    organization_name: str
    source_type: str
    endpoint_url: Optional[str]
    auth_type: Optional[str]
    parser_type: str
    refresh_interval_minutes: Optional[int]
    region: Optional[str]
    state: Optional[str]
    county: Optional[str]
    default_location_id: Optional[int]
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True