from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MeasurementCreate(BaseModel):
    user_id: int
    sample_id: int
    parameter_code: str
    value: float
    unit: Optional[str] = None
    qualifier: Optional[str] = None
    method: Optional[str] = None


class MeasurementResponse(BaseModel):
    id: int
    sample_id: int
    parameter_code: str
    value: float
    unit: Optional[str] = None
    qualifier: Optional[str] = None
    method: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True