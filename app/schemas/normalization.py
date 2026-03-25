from pydantic import BaseModel


class NormalizationResponse(BaseModel):
    ingestion_run_id: int
    raw_records_seen: int
    normalized_records_created: int
    message: str