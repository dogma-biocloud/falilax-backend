from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.source_attribution_service import get_source_attribution

router = APIRouter(prefix="/source-attribution", tags=["source-attribution"])


@router.get("/{site_id}")
def source_attribution(
    site_id: int,
    db: Session = Depends(get_db),
) -> dict:
    return get_source_attribution(db, site_id)