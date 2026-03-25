from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ParameterDefinition(Base):
    __tablename__ = "parameter_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)

    parameter_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    threshold_profile: Mapped[str | None] = mapped_column(String(64), nullable=True)
    regulatory_source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    warn_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    warn_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )