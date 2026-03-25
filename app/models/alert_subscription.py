from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    subscriber_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subscriber_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_code: Mapped[str] = mapped_column(String(128), nullable=False)

    delivery_channel: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'in_app'")
    )
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        Index("ix_alert_subscriptions_scope", "scope_type", "scope_code"),
    )