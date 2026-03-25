from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Float, ForeignKey, Index, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Measurement(Base):
    """
    Generic measurement rows:
    - parameter_code: "ph", "turbidity", "lead_ppb", etc.
    - value: numeric reading
    """
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sample_id: Mapped[int] = mapped_column(
        ForeignKey("water_samples.id"),
        nullable=False,
        index=True,
    )

    parameter_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)

    qualifier: Mapped[str | None] = mapped_column(String(8), nullable=True)  # "<", ">", "ND"
    method: Mapped[str | None] = mapped_column(String(128), nullable=True)

    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="manual",
    )

    quality_flag: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="valid",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


Index("ix_measurements_sample_param", Measurement.sample_id, Measurement.parameter_code)