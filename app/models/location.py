from __future__ import annotations

from sqlalchemy import String, Integer, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Location(Base):
    """
    A 'Location' is a water source or endpoint:
    - household tap
    - school
    - hospital
    - utility node
    - borehole / well

    This model is now fully FalilaX-aware:
    It connects locations to distribution infrastructure.
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # 🔁 Renamed conceptually (keep DB column same for now)
    type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )  # household, school, hospital, utility, etc.

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 🌍 Keep lat/lon as strings for now (we can upgrade later to Float)
    lat: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lon: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # 👤 Owner / responsible user
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # 🧠 NEW: FalilaX infrastructure links

    central_system_id: Mapped[int | None] = mapped_column(
        ForeignKey("central_systems.id"),
        nullable=True
    )

    distribution_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("distribution_lines.id"),
        nullable=True
    )

    # 🗺️ Optional: for map-level grouping (future scaling)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    county: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 🧱 Optional: UI positioning (FalilaX map rendering)
    x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[str] = mapped_column(server_default=text("now()"))