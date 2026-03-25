from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class NormalizedWaterRecord(Base):
    __tablename__ = "normalized_water_records"

    id = Column(Integer, primary_key=True, index=True)

    raw_record_id = Column(Integer, ForeignKey("raw_water_records.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False, index=True)

    location_name = Column(String(255), nullable=False)
    parameter_code = Column(String(64), nullable=False, index=True)
    parameter_name = Column(String(255), nullable=False)

    measured_value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=True)

    original_value = Column(Float, nullable=True)
    original_unit = Column(String(32), nullable=True)

    threshold = Column(Float, nullable=True)
    status = Column(String(32), nullable=False)

    sample_date = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)