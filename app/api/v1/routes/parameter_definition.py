from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.parameter_definition import ParameterDefinition
from app.schemas.parameter_definition import ParameterDefinitionResponse

router = APIRouter()


@router.get("/parameters", response_model=List[ParameterDefinitionResponse])
def list_parameters(
    category: Optional[str] = None,
    is_active: Optional[bool] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(ParameterDefinition)

    if category:
        query = query.filter(ParameterDefinition.category == category)

    if is_active is not None:
        query = query.filter(ParameterDefinition.is_active == is_active)

    return query.order_by(ParameterDefinition.parameter_code.asc()).limit(limit).all()


@router.get("/parameters/{parameter_code}", response_model=ParameterDefinitionResponse)
def get_parameter(
    parameter_code: str,
    db: Session = Depends(get_db),
):
    parameter = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.parameter_code == parameter_code)
        .first()
    )

    if not parameter:
        raise HTTPException(status_code=404, detail="Parameter not found")

    return parameter