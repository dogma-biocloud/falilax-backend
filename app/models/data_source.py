from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)

    source_name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=False)

    source_type = Column(String(50), nullable=False)
    endpoint_url = Column(Text, nullable=True)
    auth_type = Column(String(50), nullable=True)
    parser_type = Column(String(50), nullable=False, default="generic")
    refresh_interval_minutes = Column(Integer, nullable=True)

    region = Column(String(255), nullable=True)
    state = Column(String(100), nullable=True)
    county = Column(String(100), nullable=True)

    default_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )