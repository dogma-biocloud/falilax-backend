from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.alert import Alert
from app.models.location import Location
from app.models.measurement import Measurement
from app.models.water_sample import WaterSample
from app.schemas.map import MapNetworkResponse

router = APIRouter(prefix="/map", tags=["Map"])


ALABAMA_COUNTY_COORDS: dict[str, tuple[int, int]] = {
    "lauderdale": (8, 10),
    "limestone": (18, 10),
    "madison": (28, 10),
    "jackson": (40, 10),

    "colbert": (8, 18),
    "lawrence": (18, 18),
    "morgan": (28, 18),
    "marshall": (38, 18),
    "dekalb": (48, 18),

    "franklin": (8, 26),
    "winston": (18, 26),
    "cullman": (28, 26),
    "blount": (38, 26),
    "cherokee": (48, 26),

    "marion": (8, 34),
    "walker": (18, 34),
    "jefferson": (28, 34),
    "st_clair": (38, 34),
    "etowah": (48, 34),
    "calhoun": (58, 34),
    "cleburne": (68, 34),

    "fayette": (8, 42),
    "tuscaloosa": (18, 42),
    "shelby": (28, 42),
    "talladega": (38, 42),
    "clay": (48, 42),
    "randolph": (58, 42),

    "pickens": (8, 50),
    "greene": (18, 50),
    "bibb": (28, 50),
    "chilton": (38, 50),
    "coosa": (48, 50),
    "tallapoosa": (58, 50),
    "chambers": (68, 50),
    "lee": (78, 50),

    "sumter": (8, 58),
    "hale": (18, 58),
    "perry": (28, 58),
    "dallas": (38, 58),
    "autauga": (48, 58),
    "elmore": (58, 58),
    "macon": (68, 58),
    "russell": (78, 58),

    "choctaw": (8, 66),
    "marengo": (18, 66),
    "wilcox": (28, 66),
    "lowndes": (38, 66),
    "montgomery": (48, 66),
    "bullock": (58, 66),
    "barbour": (68, 66),

    "washington": (12, 78),
    "clarke": (24, 78),
    "monroe": (36, 78),
    "butler": (48, 78),
    "crenshaw": (58, 78),
    "pike": (68, 78),
    "coffee": (78, 78),
    "dale": (88, 78),

    "mobile": (18, 90),
    "baldwin": (30, 92),
    "escambia": (48, 90),
    "conecuh": (58, 90),
    "covington": (68, 90),
    "geneva": (80, 90),
    "henry": (90, 90),
    "houston": (94, 82),
}

ALABAMA_SITE_OFFSETS: list[tuple[int, int]] = [
    (0, 0),
    (6, -4),
    (-6, 4),
    (8, 6),
    (-8, -6),
    (12, 0),
    (0, 10),
    (-12, 0),
    (0, -10),
]


def clamp_percent(value: int, minimum: int = 6, maximum: int = 94) -> int:
    return max(minimum, min(maximum, value))


def get_dynamic_site_position(
    *,
    state_code: str,
    county_code: str,
    site_index: int,
) -> tuple[int, int]:
    """
    Place site pins around a county anchor point so multiple facilities
    in one county do not stack on each other.
    """
    if state_code == "AL" and county_code in ALABAMA_COUNTY_COORDS:
        base_x, base_y = ALABAMA_COUNTY_COORDS[county_code]
    else:
        base_x, base_y = 50, 50

    offset_x, offset_y = ALABAMA_SITE_OFFSETS[site_index % len(ALABAMA_SITE_OFFSETS)]

    ring = site_index // len(ALABAMA_SITE_OFFSETS)
    spread = ring * 4

    x = clamp_percent(base_x + offset_x + (spread if offset_x >= 0 else -spread))
    y = clamp_percent(base_y + offset_y + (spread if offset_y >= 0 else -spread))

    return x, y


def normalize_status_from_tier(tier: str | None) -> str:
    tier_value = str(tier or "").upper()

    if tier_value == "CRITICAL":
        return "critical"
    if tier_value in {"ACTION", "NOTICE"}:
        return "moderate"
    return "safe"


def combine_status(current: str, new: str) -> str:
    order = {"safe": 0, "moderate": 1, "critical": 2}
    return new if order.get(new, 0) > order.get(current, 0) else current


@router.get("/network", response_model=MapNetworkResponse)
def get_map_network() -> MapNetworkResponse:
    return MapNetworkResponse(
        nodes=[
            {
                "id": "source",
                "label": "Central Source",
                "x": 10,
                "y": 48,
                "status": "safe",
                "type": "source",
                "detail": "Source water stable",
                "response": "Continue routine monitoring and maintain baseline source testing.",
            },
            {
                "id": "line-a",
                "label": "Distribution Line A",
                "x": 30,
                "y": 48,
                "status": "moderate",
                "type": "distribution",
                "detail": "Minor shared-line disturbance",
                "response": "Inspect line pressure behavior and test adjacent downstream nodes.",
            },
            {
                "id": "district-5",
                "label": "District 5",
                "x": 50,
                "y": 48,
                "status": "moderate",
                "type": "distribution",
                "detail": "Monitoring active",
                "response": "Increase local sampling frequency and compare with nearby district branches.",
            },
            {
                "id": "school",
                "label": "Lincoln Elementary",
                "x": 74,
                "y": 28,
                "status": "critical",
                "type": "school",
                "detail": "Highest endpoint concern",
                "response": "Escalate response immediately, isolate affected fixtures, and confirm with certified testing.",
            },
            {
                "id": "hospital",
                "label": "Hospital Zone",
                "x": 74,
                "y": 50,
                "status": "moderate",
                "type": "hospital",
                "detail": "Precautionary monitoring",
                "response": "Maintain precautionary surveillance and prioritize patient-facing fixtures.",
            },
            {
                "id": "homes",
                "label": "Residential Cluster",
                "x": 74,
                "y": 72,
                "status": "safe",
                "type": "residential",
                "detail": "No elevated risk detected",
                "response": "Maintain standard observation and compare against district-level shifts.",
            },
        ],
        edges=[
            {"from": "source", "to": "line-a", "severity": "safe"},
            {"from": "line-a", "to": "district-5", "severity": "moderate"},
            {"from": "district-5", "to": "school", "severity": "critical"},
            {"from": "district-5", "to": "hospital", "severity": "moderate"},
            {"from": "district-5", "to": "homes", "severity": "safe"},
        ],
    )


@router.get("/usa-summary")
def get_usa_summary(db: Session = Depends(get_db)) -> dict:
    alerts = db.execute(select(Alert)).scalars().all()

    state_buckets: dict[str, dict] = defaultdict(
        lambda: {
            "state_name": None,
            "alert_count": 0,
            "has_critical": False,
            "has_monitoring": False,
        }
    )

    for alert in alerts:
        state_code = getattr(alert, "state_region", None) or "UNKNOWN"
        state_code = str(state_code).upper()

        state_buckets[state_code]["state_name"] = state_code
        state_buckets[state_code]["alert_count"] += 1

        tier = str(getattr(alert, "tier", "")).upper()
        if tier == "CRITICAL":
            state_buckets[state_code]["has_critical"] = True
        elif tier in {"ACTION", "NOTICE"}:
            state_buckets[state_code]["has_monitoring"] = True

    states = []
    critical_zones = 0
    monitoring_zones = 0
    areas_requiring_attention = 0

    for state_code, bucket in state_buckets.items():
        if bucket["has_critical"]:
            status = "critical"
            critical_zones += 1
            areas_requiring_attention += 1
        elif bucket["has_monitoring"]:
            status = "moderate"
            monitoring_zones += 1
            areas_requiring_attention += 1
        else:
            status = "safe"

        states.append(
            {
                "state_code": state_code,
                "state_name": bucket["state_name"] or state_code,
                "status": status,
                "alert_count": bucket["alert_count"],
            }
        )

    states.sort(key=lambda item: item["state_code"])

    return {
        "states_monitored": len(states),
        "areas_requiring_attention": areas_requiring_attention,
        "critical_zones": critical_zones,
        "monitoring_zones": monitoring_zones,
        "states": states,
    }


@router.get("/states/{state_code}")
def get_state_detail(
    state_code: str,
    db: Session = Depends(get_db),
) -> dict:
    state_code = state_code.upper()

    alerts = (
        db.execute(
            select(Alert).where(Alert.state_region == state_code)
        )
        .scalars()
        .all()
    )

    county_buckets: dict[str, dict] = defaultdict(
        lambda: {
            "county_name": None,
            "alert_count": 0,
            "status": "safe",
        }
    )

    for alert in alerts:
        county_code = str(getattr(alert, "county_code", None) or "unknown").lower()
        county_name = county_code.replace("_", " ").title()

        county_buckets[county_code]["county_name"] = county_name
        county_buckets[county_code]["alert_count"] += 1
        county_buckets[county_code]["status"] = combine_status(
            county_buckets[county_code]["status"],
            normalize_status_from_tier(getattr(alert, "tier", None)),
        )

    counties = []
    index = 0
    for county_code, bucket in county_buckets.items():
        if state_code == "AL" and county_code in ALABAMA_COUNTY_COORDS:
            x, y = ALABAMA_COUNTY_COORDS[county_code]
        else:
            row = index // 8
            col = index % 8
            x = 10 + (col * 10)
            y = 12 + (row * 10)

        counties.append(
            {
                "county_code": county_code,
                "county_name": bucket["county_name"] or county_code.title(),
                "x": x,
                "y": y,
                "status": bucket["status"],
                "alert_count": bucket["alert_count"],
            }
        )
        index += 1

    return {
        "state_code": state_code,
        "counties": counties,
    }


@router.get("/sites")
def get_county_sites(
    state: str,
    county: str,
    db: Session = Depends(get_db),
) -> dict:
    state_code = state.upper()
    county_code = county.lower()

    rows = (
        db.query(Measurement, WaterSample, Location)
        .join(WaterSample, Measurement.sample_id == WaterSample.id)
        .join(Location, WaterSample.location_id == Location.id)
        .order_by(Measurement.measured_at.desc())
        .limit(100)
        .all()
    )

    site_buckets: dict[int, dict] = {}

    for measurement, sample, location in rows:
        location_state = str(getattr(location, "state", "") or "").upper()
        location_county = str(getattr(location, "county", "") or "").lower()

        if location_state != state_code or location_county != county_code:
            continue

        location_id = location.id
        if location_id not in site_buckets:
            site_buckets[location_id] = {
                "location": location,
                "status": "safe",
                "signals": [],
                "last_sample_at": measurement.measured_at,
            }

        site_buckets[location_id]["status"] = combine_status(
            site_buckets[location_id]["status"],
            "critical" if str(measurement.quality_flag).lower() == "critical"
            else "moderate" if str(measurement.quality_flag).lower() in {"attention", "moderate"}
            else "safe",
        )

        if len(site_buckets[location_id]["signals"]) < 4:
            site_buckets[location_id]["signals"].append(
                {
                    "label": str(measurement.parameter_code).upper(),
                    "value": f"{measurement.value} {measurement.unit or ''}".strip(),
                }
            )

    sites = []
    for idx, (location_id, bucket) in enumerate(site_buckets.items()):
        location = bucket["location"]

        x = getattr(location, "x", None)
        y = getattr(location, "y", None)

        if x is None or y is None:
            x, y = get_dynamic_site_position(
                state_code=state_code,
                county_code=county_code,
                site_index=idx,
            )

        label = getattr(location, "name", None) or f"Site {location_id}"

        location_type = str(getattr(location, "location_type", "") or "").lower()
        if "school" in location_type:
            node_type = "school"
        elif "hospital" in location_type:
            node_type = "hospital"
        elif "residential" in location_type or "home" in location_type:
            node_type = "residential"
        elif "utility" in location_type:
            node_type = "utility"
        else:
            node_type = "distribution"

        sites.append(
            {
                "id": f"location-{location_id}",
                "label": label,
                "county_code": county_code,
                "x": x,
                "y": y,
                "status": bucket["status"],
                "type": node_type,
                "detail": f"Latest monitored site status for {label}",
                "response": "Review the latest measurements, inspect the local infrastructure, and compare nearby sites.",
                "last_sample_at": bucket["last_sample_at"].isoformat() if bucket["last_sample_at"] else None,
                "signals": bucket["signals"],
            }
        )

    return {
        "state": state_code,
        "county": county_code,
        "sites": sites,
    }