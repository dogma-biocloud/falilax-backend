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

    # NEW ingestion intelligence fields
    measured_at: Optional[datetime] = None
    source_type: Optional[str] = "manual"
    quality_flag: Optional[str] = "valid"


class MeasurementResponse(BaseModel):
    id: int
    sample_id: int
    parameter_code: str
    value: float

    unit: Optional[str] = None
    qualifier: Optional[str] = None
    method: Optional[str] = None

    measured_at: datetime
    source_type: str
    quality_flag: str

    created_at: datetime

    class Config:
        from_attributes = True