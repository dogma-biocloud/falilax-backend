from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.central_system import CentralSystem
from app.schemas.central_system import CentralSystemCreate, CentralSystemRead

router = APIRouter(prefix="/central-systems", tags=["Central Systems"])


@router.post("", response_model=CentralSystemRead)
def create_central_system(
    payload: CentralSystemCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(CentralSystem)
        .filter(CentralSystem.code == payload.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Central system code already exists")

    system = CentralSystem(**payload.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.get("", response_model=list[CentralSystemRead])
def list_central_systems(db: Session = Depends(get_db)):
    return db.query(CentralSystem).order_by(CentralSystem.id.desc()).all()


@router.get("/{system_id}", response_model=CentralSystemRead)
def get_central_system(system_id: int, db: Session = Depends(get_db)):
    system = (
        db.query(CentralSystem)
        .filter(CentralSystem.id == system_id)
        .first()
    )
    if not system:
        raise HTTPException(status_code=404, detail="Central system not found")
    return system