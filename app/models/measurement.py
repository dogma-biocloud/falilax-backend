from __future__ import annotations

from sqlalchemy import Integer, String, Float, ForeignKey, text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Measurement(Base):
    """
    Generic measurement rows:
    - parameter_code: "ph", "turbidity_ntu", "e_coli_cfu_100ml", "lead_ug_l"
    - value: numeric reading
    This design prevents schema fragmentation as parameters expand.
    """
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sample_id: Mapped[int] = mapped_column(ForeignKey("water_samples.id"), nullable=False)

    parameter_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)

    qualifier: Mapped[str | None] = mapped_column(String(8), nullable=True)  # "<", ">", "ND"
    method: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[str] = mapped_column(server_default=text("now()"))


Index("ix_measurements_sample_param", Measurement.sample_id, Measurement.parameter_code)