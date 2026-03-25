from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass(frozen=True)
class ClusterRiskResult:
    """
    Result of cluster-level risk evaluation.
    """
    cluster_code: str
    risk_level: str  # "OK" | "NOTICE" | "ACTION"
    message: str
    affected_sites: int
    trigger_parameters: tuple[str, ...]


class ClusterRiskEngine:
    """
    Detects cluster-level contamination patterns across multiple sites.

    Purpose:
    - Identify regional patterns that single-site alerts cannot detect.
    - Escalate alerts when multiple nearby sites show similar issues.
    """

    def evaluate(
        self,
        cluster_code: str,
        site_measurements: List[Dict],
        window_minutes: int = 120,
    ) -> Optional[ClusterRiskResult]:
        """
        site_measurements example:

        [
            {"site_id": "A1", "parameter": "turbidity", "value": 8.1, "timestamp": ...},
            {"site_id": "A2", "parameter": "turbidity", "value": 7.9, "timestamp": ...},
            {"site_id": "A3", "parameter": "chlorine", "value": 0.1, "timestamp": ...}
        ]
        """

        if not site_measurements:
            return None

        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        recent = [
            m for m in site_measurements
            if m.get("timestamp") and m["timestamp"] >= window_start
        ]

        if not recent:
            return None

        parameter_counts: Dict[str, set] = {}

        for m in recent:
            parameter = m.get("parameter")
            site_id = m.get("site_id")

            if not parameter or not site_id:
                continue

            if parameter not in parameter_counts:
                parameter_counts[parameter] = set()

            parameter_counts[parameter].add(site_id)

        for parameter, sites in parameter_counts.items():

            site_count = len(sites)

            if site_count >= 3:
                return ClusterRiskResult(
                    cluster_code=cluster_code,
                    risk_level="ACTION",
                    message=f"Multiple sites reporting abnormal {parameter} levels across cluster.",
                    affected_sites=site_count,
                    trigger_parameters=(parameter,),
                )

            if site_count == 2:
                return ClusterRiskResult(
                    cluster_code=cluster_code,
                    risk_level="NOTICE",
                    message=f"Possible emerging cluster issue detected for {parameter}.",
                    affected_sites=site_count,
                    trigger_parameters=(parameter,),
                )

        return None