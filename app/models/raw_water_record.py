from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RawWaterRecord(Base):
    __tablename__ = "raw_water_records"

    id = Column(Integer, primary_key=True, index=True)

    source_id = Column(
        Integer,
        ForeignKey("data_sources.id"),
        nullable=False,
        index=True,
    )

    ingestion_run_id = Column(
        Integer,
        ForeignKey("ingestion_runs.id"),
        nullable=False,
        index=True,
    )

    external_record_id = Column(
        String(255),
        nullable=True,
        index=True,
    )

    payload = Column(
        JSON,
        nullable=False,
    )

    parsing_status = Column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    source = relationship("DataSource", backref="raw_water_records")
    ingestion_run = relationship("IngestionRun", backref="raw_water_records")