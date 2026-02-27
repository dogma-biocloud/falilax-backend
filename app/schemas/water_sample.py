from datetime import datetime
from pydantic import BaseModel

class WaterSampleResponse(BaseModel):
    id: int
    location_id: int
    collected_by_user_id: int | None
    collected_at: datetime
    method: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True