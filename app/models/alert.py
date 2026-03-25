from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Alert(Base):
    """
    Calm, tiered notifications (FalilaX).

    Target scope: who/where we notify (household/school/hospital/water_sample/etc)
    Origin scope: likely source (central system / distribution line / site)
    Geo routing: cluster/region/county
    Delivery: in_app/email/sms + scheduling
    Dedupe: (user + scope + tier + parameter) collapses repeats into one row
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Target scope
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Tiering
    tier: Mapped[str] = mapped_column(String(16), nullable=False)  # NOTICE / ACTION / CRITICAL
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1500), nullable=False)

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'queued'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Dedupe helpers
    parameter_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default=text("'unknown'"),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    occurrence_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    # Delivery / retry tracking
    delivery_channel: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'in_app'"),
    )
    recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivery_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Source attribution
    origin_scope_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'unknown'"),
    )
    origin_scope_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Geo routing
    cluster_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    county_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Safety / disclaimers
    confidence: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'suspected'"),
    )
    disclaimer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Location context
    location_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    plus_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    directions_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_alert_scope", "scope_type", "scope_id"),
        Index("ix_alerts_delivery_queue", "status", "scheduled_for"),
        Index("ix_alerts_origin_scope", "origin_scope_type", "origin_scope_id"),
        Index("ix_alerts_geo", "cluster_code", "region_code", "county_code"),
        Index(
            "ux_alerts_dedupe",
            "user_id",
            "scope_type",
            "scope_id",
            "tier",
            "parameter_code",
            unique=True,
        ),
    )