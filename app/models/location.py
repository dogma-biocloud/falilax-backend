from __future__ import annotations

from sqlalchemy import String, Integer, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Location(Base):
    """
    A 'Location' is a water source point (household tap, borehole, well, school, utility tap, etc.)
    """
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # household_tap, borehole, well, river, school, utility, etc.

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    lat: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lon: Mapped[str | None] = mapped_column(String(32), nullable=True)

    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[str] = mapped_column(server_default=text("now()"))