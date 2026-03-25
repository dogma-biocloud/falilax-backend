from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.simulation_service import SimulationConfig, simulate_measurement_cycle

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/run")
def run_simulation_cycle(
    user_id: int = Query(...),
    sample_id: int = Query(...),

    # geographic hierarchy
    cluster_code: str | None = Query(default=None),
    region_code: str | None = Query(default=None),
    county_code: str | None = Query(default=None),
    state_region: str | None = Query(default=None),
    country: str | None = Query(default=None),

    # location metadata
    location_label: str | None = Query(default=None),
    address_line1: str | None = Query(default=None),
    address_line2: str | None = Query(default=None),
    city: str | None = Query(default=None),
    postal_code: str | None = Query(default=None),
    plus_code: str | None = Query(default=None),
    landmark: str | None = Query(default=None),
    directions_hint: str | None = Query(default=None),

    # optional source attribution hints
    origin_scope_type: str = Query(default="site"),
    origin_scope_id: int | None = Query(default=None),

    # optional parameter override
    parameters: str | None = Query(
        default=None,
        description="Comma-separated parameter list, e.g. ph,turbidity,chlorine",
    ),

    db: Session = Depends(get_db),
) -> dict:
    """
    Run one simulation cycle and push the generated measurements
    through the real FalilaX measurement + alert pipeline.
    """

    config = SimulationConfig(
        user_id=user_id,
        sample_id=sample_id,
        cluster_code=cluster_code,
        region_code=region_code,
        county_code=county_code,
        state_region=state_region,
        country=country,
        location_label=location_label,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        postal_code=postal_code,
        plus_code=plus_code,
        landmark=landmark,
        directions_hint=directions_hint,
        origin_scope_type=origin_scope_type,
        origin_scope_id=origin_scope_id if origin_scope_id is not None else sample_id,
    )

    parsed_parameters: list[str] | None = None
    if parameters:
        parsed_parameters = [p.strip() for p in parameters.split(",") if p.strip()]

    generated = simulate_measurement_cycle(
        db,
        config=config,
        parameters=parsed_parameters,
    )

    return {
        "message": "Simulation cycle completed",
        "generated_count": len(generated),
        "sample_id": sample_id,
        "location_label": location_label,
        "measurements": generated,
    }