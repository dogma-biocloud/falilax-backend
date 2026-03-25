from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.central_system import CentralSystem
from app.models.distribution_line import DistributionLine
from app.schemas.distribution_line import DistributionLineCreate, DistributionLineRead

router = APIRouter(prefix="/distribution-lines", tags=["Distribution Lines"])


@router.post("", response_model=DistributionLineRead)
def create_distribution_line(
    payload: DistributionLineCreate,
    db: Session = Depends(get_db),
):
    central_system = (
        db.query(CentralSystem)
        .filter(CentralSystem.id == payload.central_system_id)
        .first()
    )
    if not central_system:
        raise HTTPException(status_code=400, detail="Central system does not exist")

    existing = (
        db.query(DistributionLine)
        .filter(DistributionLine.line_code == payload.line_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Distribution line code already exists")

    line = DistributionLine(**payload.model_dump())
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


@router.get("", response_model=list[DistributionLineRead])
def list_distribution_lines(
    central_system_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DistributionLine)

    if central_system_id is not None:
        query = query.filter(DistributionLine.central_system_id == central_system_id)

    return query.order_by(DistributionLine.id.desc()).all()


@router.get("/{line_id}", response_model=DistributionLineRead)
def get_distribution_line(line_id: int, db: Session = Depends(get_db)):
    line = (
        db.query(DistributionLine)
        .filter(DistributionLine.id == line_id)
        .first()
    )
    if not line:
        raise HTTPException(status_code=404, detail="Distribution line not found")
    return line