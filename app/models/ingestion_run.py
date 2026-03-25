from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)

    source_id = Column(
        Integer,
        ForeignKey("data_sources.id"),
        nullable=False,
        index=True,
    )

    source = relationship("DataSource", backref="ingestion_runs")

    status = Column(
        String(50),
        nullable=False,
        default="started",
        index=True,
    )

    records_extracted = Column(
        Integer,
        nullable=False,
        default=0,
    )

    records_loaded = Column(
        Integer,
        nullable=False,
        default=0,
    )

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    finished_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    log_summary = Column(
        Text,
        nullable=True,
    )