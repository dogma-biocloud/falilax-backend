from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AlertIngestRequest(BaseModel):
    user_id: int
    sample_id: int
    parameter_code: str = Field(..., max_length=64)
    value: float
    unit: Optional[str] = Field(default=None, max_length=32)

    # geo routing
    cluster_code: Optional[str] = Field(default=None, max_length=64)
    region_code: Optional[str] = Field(default=None, max_length=64)
    county_code: Optional[str] = Field(default=None, max_length=64)
    state_region: Optional[str] = Field(default=None, max_length=64)
    country: Optional[str] = Field(default=None, max_length=64)

    # location context
    location_label: Optional[str] = Field(default=None, max_length=255)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=128)
    postal_code: Optional[str] = Field(default=None, max_length=32)
    plus_code: Optional[str] = Field(default=None, max_length=32)
    landmark: Optional[str] = Field(default=None, max_length=255)
    directions_hint: Optional[str] = Field(default=None, max_length=255)

    # attribution
    origin_scope_type: str = Field(default="unknown", max_length=32)
    origin_scope_id: Optional[int] = None


class AlertIngestResponse(BaseModel):
    message: str
    measurement_id: int