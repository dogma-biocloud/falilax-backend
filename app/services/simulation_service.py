from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Iterable

from sqlalchemy.orm import Session

from app.services.measurement_pipeline import create_measurement_and_alerts


@dataclass(frozen=True)
class SimulationConfig:
    user_id: int
    sample_id: int

    # geographic hierarchy
    cluster_code: str | None = None
    region_code: str | None = None
    county_code: str | None = None
    state_region: str | None = None
    country: str | None = None

    # location metadata
    location_label: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    plus_code: str | None = None
    landmark: str | None = None
    directions_hint: str | None = None

    # source attribution hints
    origin_scope_type: str = "site"
    origin_scope_id: Optional[int] = None


# ---------------------------------------------------------
# Parameter value generators
# ---------------------------------------------------------

def _sample_value(parameter_code: str) -> tuple[float, str | None]:
    """
    Generate semi-realistic values with occasional anomalies.
    """

    p = parameter_code.lower()

    # pH
    if p == "ph":
        if random.random() < 0.18:
            return round(
                random.choice([
                    random.uniform(3.0, 5.5),
                    random.uniform(9.0, 11.0),
                ]),
                2,
            ), "pH"

        return round(random.uniform(6.6, 8.2), 2), "pH"

    # Turbidity
    if p == "turbidity":
        if random.random() < 0.20:
            return round(random.uniform(5.5, 15.0), 2), "NTU"

        return round(random.uniform(0.1, 3.0), 2), "NTU"

    # Chlorine
    if p == "chlorine":
        if random.random() < 0.15:
            return round(random.uniform(0.0, 0.15), 2), "mg/L"

        return round(random.uniform(0.2, 1.2), 2), "mg/L"

    # Lead
    if p == "lead":
        if random.random() < 0.12:
            return round(random.uniform(0.011, 0.05), 4), "mg/L"

        return round(random.uniform(0.0, 0.008), 4), "mg/L"

    # Nitrate
    if p == "nitrate":
        if random.random() < 0.15:
            return round(random.uniform(10.5, 25.0), 2), "mg/L"

        return round(random.uniform(0.5, 8.0), 2), "mg/L"

    # E. coli
    if p == "ecoli":
        if random.random() < 0.08:
            return 1.0, "cfu/100ml"

        return 0.0, "cfu/100ml"

    # fallback
    return round(random.uniform(0.0, 10.0), 2), None


# ---------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------

DEFAULT_PARAMETERS = (
    "ph",
    "turbidity",
    "chlorine",
    "lead",
    "nitrate",
    "ecoli",
)


def simulate_measurement_cycle(
    db: Session,
    *,
    config: SimulationConfig,
    parameters: Iterable[str] | None = None,
) -> list[dict]:
    """
    Simulate one cycle of measurements across multiple parameters.

    Each generated measurement goes through the **real alert pipeline**.
    """

    if parameters is None:
        parameters = DEFAULT_PARAMETERS

    generated: list[dict] = []

    for parameter_code in parameters:
        value, unit = _sample_value(parameter_code)

        measurement = create_measurement_and_alerts(
            db=db,
            user_id=config.user_id,
            sample_id=config.sample_id,
            parameter_code=parameter_code,
            value=value,
            unit=unit,

            cluster_code=config.cluster_code,
            region_code=config.region_code,
            county_code=config.county_code,
            state_region=config.state_region,
            country=config.country,

            location_label=config.location_label,
            address_line1=config.address_line1,
            address_line2=config.address_line2,
            city=config.city,
            postal_code=config.postal_code,
            plus_code=config.plus_code,
            landmark=config.landmark,
            directions_hint=config.directions_hint,

            origin_scope_type=config.origin_scope_type,
            origin_scope_id=config.origin_scope_id,
        )

        generated.append(
            {
                "measurement_id": measurement.id,
                "parameter_code": parameter_code,
                "value": value,
                "unit": unit,
            }
        )

    return generated