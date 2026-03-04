from datetime import datetime
from pydantic import BaseModel


# ============================
# Response Schema (Read)
# ============================
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


# ============================
# Create Schema (Write)
# ============================
class WaterSampleCreate(BaseModel):
    location_id: int
    collected_by_user_id: int | None = None
    collected_at: datetime | None = None
    method: str
    notes: str | None = None