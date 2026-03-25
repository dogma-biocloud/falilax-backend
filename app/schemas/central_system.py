from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CentralSystemCreate(BaseModel):
    code: str
    name: str
    region: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    is_active: bool = True


class CentralSystemRead(BaseModel):
    id: int
    code: str
    name: str
    region: Optional[str]
    state: Optional[str]
    county: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True