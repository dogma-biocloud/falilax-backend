from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Alert(Base):
    """
    Calm, tiered notifications (not 'Amber Alerts').
    Alerts attach to a scope so they can target sample/location/zone later.
    """
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)  # sample/location/zone
    scope_id: Mapped[int] = mapped_column(Integer, nullable=False)

    tier: Mapped[str] = mapped_column(String(16), nullable=False)  # green/yellow/orange/red
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1500), nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'queued'"))  # queued/sent/read/failed

    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
    sent_at: Mapped[str | None] = mapped_column(nullable=True)


Index("ix_alert_scope", Alert.scope_type, Alert.scope_id)