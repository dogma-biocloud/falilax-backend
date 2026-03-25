from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceRead

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@router.post("", response_model=DataSourceRead)
def create_data_source(payload: DataSourceCreate, db: Session = Depends(get_db)):
    source = DataSource(
        source_name=payload.source_name,
        organization_name=payload.organization_name,
        source_type=payload.source_type,
        endpoint_url=payload.endpoint_url,
        auth_type=payload.auth_type,
        parser_type=payload.parser_type,
        refresh_interval_minutes=payload.refresh_interval_minutes,
        region=payload.region,
        state=payload.state,
        county=payload.county,
        default_location_id=payload.default_location_id,
        created_by_user_id=1,  # temporary until auth/current_user is wired
        is_active=payload.is_active,
        notes=payload.notes,
    )

    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("", response_model=list[DataSourceRead])
def list_data_sources(db: Session = Depends(get_db)):
    return db.query(DataSource).order_by(DataSource.id.desc()).all()


@router.get("/{source_id}", response_model=DataSourceRead)
def get_data_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source