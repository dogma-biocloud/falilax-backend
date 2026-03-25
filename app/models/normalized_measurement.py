from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class NormalizedMeasurement(Base):
    __tablename__ = "normalized_measurements"

    id = Column(Integer, primary_key=True, index=True)

    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    raw_record_id = Column(Integer, ForeignKey("raw_water_records.id"), nullable=False)

    location_name = Column(String(255), nullable=True)
    parameter_code = Column(String(100), nullable=False)
    parameter_name = Column(String(255), nullable=False)

    measured_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)

    sample_date = Column(DateTime(timezone=True), nullable=True)

    quality_flag = Column(String(50), nullable=False, default="valid")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)