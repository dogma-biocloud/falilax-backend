from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import DataSource
from app.schemas.sensor_ingest import SensorIngestRequest
from app.services.sensor_ingestion_service import ingest_sensor_payload

router = APIRouter(prefix="/sensor-ingest", tags=["Sensor Ingestion"])


@router.post("/{source_id}")
def ingest_sensor_reading(
    source_id: int,
    payload: SensorIngestRequest,
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
        result = ingest_sensor_payload(
            db=db,
            source=source,
            payload=payload,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))