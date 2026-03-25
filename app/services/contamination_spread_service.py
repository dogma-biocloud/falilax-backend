from __future__ import annotations

from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Any

from sqlalchemy.orm import Session

from app.models.location import Location
from app.models.measurement import Measurement
from app.models.water_sample import WaterSample


@dataclass
class SpreadSite:
    location_id: int
    location_name: str
    latitude: float | None
    longitude: float | None
    measured_at: Any
    value: float
    quality_flag: str


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    r = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def get_recent_abnormal_sites(
    db: Session,
    *,
    parameter_code: str,
    limit: int = 100,
) -> list[SpreadSite]:
    rows = (
        db.query(
            Measurement,
            WaterSample,
            Location,
        )
        .join(WaterSample, Measurement.sample_id == WaterSample.id)
        .join(Location, WaterSample.location_id == Location.id)
        .filter(Measurement.parameter_code == parameter_code)
        .filter(Measurement.quality_flag.in_(["attention", "critical"]))
        .order_by(Measurement.measured_at.desc())
        .limit(limit)
        .all()
    )

    sites: list[SpreadSite] = []
    for measurement, sample, location in rows:
        sites.append(
            SpreadSite(
                location_id=location.id,
                location_name=getattr(location, "name", f"Location {location.id}"),
                latitude=getattr(location, "latitude", None),
                longitude=getattr(location, "longitude", None),
                measured_at=measurement.measured_at,
                value=measurement.value,
                quality_flag=measurement.quality_flag,
            )
        )

    return sites


def build_spread_clusters(
    sites: list[SpreadSite],
    *,
    radius_km: float = 5.0,
) -> list[dict]:
    clusters: list[dict] = []
    visited: set[int] = set()

    for i, site in enumerate(sites):
        if i in visited:
            continue

        cluster_sites = [site]
        visited.add(i)

        if site.latitude is None or site.longitude is None:
            clusters.append(
                {
                    "cluster_status": "unmapped",
                    "site_count": 1,
                    "sites": [site.__dict__],
                    "center_latitude": None,
                    "center_longitude": None,
                }
            )
            continue

        for j, other in enumerate(sites):
            if j in visited:
                continue
            if other.latitude is None or other.longitude is None:
                continue

            distance = haversine_km(
                site.latitude,
                site.longitude,
                other.latitude,
                other.longitude,
            )

            if distance <= radius_km:
                cluster_sites.append(other)
                visited.add(j)

        latitudes = [s.latitude for s in cluster_sites if s.latitude is not None]
        longitudes = [s.longitude for s in cluster_sites if s.longitude is not None]

        cluster_status = "isolated" if len(cluster_sites) == 1 else "clustered"
        if len(cluster_sites) >= 3:
            cluster_status = "spreading"

        clusters.append(
            {
                "cluster_status": cluster_status,
                "site_count": len(cluster_sites),
                "center_latitude": sum(latitudes) / len(latitudes) if latitudes else None,
                "center_longitude": sum(longitudes) / len(longitudes) if longitudes else None,
                "sites": [s.__dict__ for s in cluster_sites],
            }
        )

    return clusters


def analyze_contamination_spread(
    db: Session,
    *,
    parameter_code: str,
) -> dict:
    sites = get_recent_abnormal_sites(
        db,
        parameter_code=parameter_code,
    )

    clusters = build_spread_clusters(sites)

    overall_status = "none"
    if clusters:
        overall_status = "isolated"
        if any(cluster["cluster_status"] == "clustered" for cluster in clusters):
            overall_status = "clustered"
        if any(cluster["cluster_status"] == "spreading" for cluster in clusters):
            overall_status = "spreading"

    return {
        "parameter_code": parameter_code,
        "abnormal_site_count": len(sites),
        "cluster_count": len(clusters),
        "overall_status": overall_status,
        "clusters": clusters,
    }