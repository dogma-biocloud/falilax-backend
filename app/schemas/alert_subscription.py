from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertSubscriptionCreate(BaseModel):
    subscriber_type: str = Field(..., max_length=32)
    subscriber_id: Optional[int] = None
    scope_type: str = Field(..., max_length=32)
    scope_code: str = Field(..., max_length=128)
    delivery_channel: str = Field(default="in_app", max_length=16)
    recipient: Optional[str] = Field(default=None, max_length=255)
    is_enabled: bool = True


class AlertSubscriptionUpdate(BaseModel):
    delivery_channel: Optional[str] = Field(default=None, max_length=16)
    recipient: Optional[str] = Field(default=None, max_length=255)
    is_enabled: Optional[bool] = None


class AlertSubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscriber_type: str
    subscriber_id: Optional[int]
    scope_type: str
    scope_code: str
    delivery_channel: str
    recipient: Optional[str]
    is_enabled: bool
    created_at: datetime