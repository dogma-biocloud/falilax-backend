from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SensorReadings(BaseModel):
    ph: float | None = None
    turbidity: float | None = None
    chlorine: float | None = None
    lead: float | None = None
    copper: float | None = None
    nitrate: float | None = None


class SensorIngestRequest(BaseModel):
    device_id: str = Field(..., max_length=128)
    recorded_at: datetime
    location_name: str = Field(..., max_length=255)
    readings: SensorReadings
    notes: Optional[str] = None