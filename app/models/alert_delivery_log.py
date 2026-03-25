from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AlertDeliveryLog(Base):
    __tablename__ = "alert_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
    )

    parameter_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    escalation_level: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient_target: Mapped[str] = mapped_column(String(255), nullable=False)

    delivery_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="queued",
        index=True,
    )  # queued, sent, failed

    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )