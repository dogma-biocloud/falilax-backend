from __future__ import annotations

import asyncio
import logging
import os

from app.db.session import SessionLocal
from app.services.simulation_service import SimulationConfig, simulate_measurement_cycle

log = logging.getLogger(__name__)


def _env_bool(name: str, default: str = "false") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def build_demo_simulation_config() -> SimulationConfig:
    """
    Build simulation config from environment variables.
    Safe defaults are provided for demo mode.
    """
    user_id = _env_int("FALILAX_SIM_USER_ID", 1)
    sample_id = _env_int("FALILAX_SIM_SAMPLE_ID", 7)

    return SimulationConfig(
        user_id=user_id,
        sample_id=sample_id,
        cluster_code=os.getenv("FALILAX_SIM_CLUSTER_CODE", "AL-BHM-CL01"),
        region_code=os.getenv("FALILAX_SIM_REGION_CODE", "AL-JEFF"),
        county_code=os.getenv("FALILAX_SIM_COUNTY_CODE", "JEFFERSON"),
        state_region=os.getenv("FALILAX_SIM_STATE_REGION", "AL"),
        country=os.getenv("FALILAX_SIM_COUNTRY", "USA"),
        location_label=os.getenv("FALILAX_SIM_LOCATION_LABEL", "Apt F"),
        address_line1=os.getenv("FALILAX_SIM_ADDRESS_LINE1", None),
        address_line2=os.getenv("FALILAX_SIM_ADDRESS_LINE2", None),
        city=os.getenv("FALILAX_SIM_CITY", "Birmingham"),
        postal_code=os.getenv("FALILAX_SIM_POSTAL_CODE", None),
        plus_code=os.getenv("FALILAX_SIM_PLUS_CODE", None),
        landmark=os.getenv("FALILAX_SIM_LANDMARK", None),
        directions_hint=os.getenv("FALILAX_SIM_DIRECTIONS_HINT", None),
        origin_scope_type=os.getenv("FALILAX_SIM_ORIGIN_SCOPE_TYPE", "site"),
        origin_scope_id=_env_int("FALILAX_SIM_ORIGIN_SCOPE_ID", sample_id),
    )


async def simulation_loop() -> None:
    """
    Background loop for demo-mode simulated measurements.
    """
    interval_seconds = _env_int("FALILAX_SIM_INTERVAL_SECONDS", 30)
    config = build_demo_simulation_config()

    log.info(
        "FalilaX simulation loop starting",
        extra={
            "interval_seconds": interval_seconds,
            "sample_id": config.sample_id,
            "location_label": config.location_label,
        },
    )

    while True:
        db = SessionLocal()
        try:
            generated = simulate_measurement_cycle(db, config=config)
            log.info(
                "FalilaX simulation cycle completed",
                extra={
                    "generated_count": len(generated),
                    "sample_id": config.sample_id,
                    "location_label": config.location_label,
                },
            )
        except Exception:
            log.exception("FalilaX simulation cycle failed")
        finally:
            db.close()

        await asyncio.sleep(interval_seconds)


def should_run_simulation() -> bool:
    return _env_bool("FALILAX_DEMO_MODE", "false") and _env_bool("FALILAX_AUTO_SIMULATION", "true")