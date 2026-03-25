from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IngestionRunRead(BaseModel):
    id: int
    source_id: int
    status: str
    records_extracted: int
    records_loaded: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    log_summary: Optional[str] = None

    class Config:
        from_attributes = True


class FileIngestionResponse(BaseModel):
    message: str
    source_id: int
    ingestion_run_id: int
    filename: str
    records_extracted: int
    records_loaded: int
    status: str