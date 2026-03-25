from __future__ import annotations

import time

from app.db.session import SessionLocal
from app.services.simulation_service import SimulationConfig, simulate_measurement_cycle


def run_forever(
    *,
    interval_seconds: int = 30,
    user_id: int = 1,
    sample_id: int = 7,
    cluster_code: str | None = "AL-BHM-CL01",
    region_code: str | None = "AL-JEFF",
    county_code: str | None = "JEFFERSON",
    state_region: str | None = "AL",
    country: str | None = "USA",
    location_label: str | None = "Apt F",
) -> None:
    while True:
        db = SessionLocal()
        try:
            config = SimulationConfig(
                user_id=user_id,
                sample_id=sample_id,
                cluster_code=cluster_code,
                region_code=region_code,
                county_code=county_code,
                state_region=state_region,
                country=country,
                location_label=location_label,
                origin_scope_type="site",
                origin_scope_id=sample_id,
            )
            generated = simulate_measurement_cycle(db, config=config)
            print(f"Generated {len(generated)} measurements")
        finally:
            db.close()

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_forever()