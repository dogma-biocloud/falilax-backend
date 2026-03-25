from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import DataSource
from app.services.ingestion_service import ingest_rows_for_source

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/run/{source_id}")
def run_ingestion(
    source_id: int,
    rows: list[dict],
    db: Session = Depends(get_db),
):
    source = (
        db.query(DataSource)
        .filter(DataSource.id == source_id)
        .filter(DataSource.is_active.is_(True))
        .first()
    )

    if not source:
        raise HTTPException(status_code=404, detail="Active data source not found")

    try:
        run = ingest_rows_for_source(
            db=db,
            source=source,
            rows=rows,
        )
        db.commit()
        db.refresh(run)

    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "message": "Ingestion completed successfully",
        "source_id": source.id,
        "ingestion_run_id": run.id,
        "status": run.status,
        "records_extracted": run.records_extracted,
        "records_loaded": run.records_loaded,
    }