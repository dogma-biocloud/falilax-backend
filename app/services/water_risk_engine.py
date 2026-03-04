from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RiskResult:
    risk_level: str
    message: str
    trigger_parameters: tuple[str, ...]


class WaterRiskEngine:
    """
    Multi-parameter risk detection engine.

    Analyzes combinations of water quality parameters to detect higher-level
    risks (e.g. microbial contamination, corrosion, agricultural contamination).

    Design notes:
      - Prefer "confirmed" signals (e.g., E. coli presence) over inferred signals.
      - Use explicit `is not None` checks so 0.0 values are handled correctly.
      - Returns the first matching rule (priority order matters).
    """

    def evaluate(self, parameters: Dict[str, float]) -> Optional[RiskResult]:
        """
        Example input:
        {
            "ph": 5.2,
            "turbidity": 8.5,
            "chlorine": 0.1,
            "lead": 0.02,
            "ecoli": 1,
            "nitrate": 12
        }
        """

        ph = parameters.get("ph")
        turbidity = parameters.get("turbidity")
        chlorine = parameters.get("chlorine")
        lead = parameters.get("lead")
        ecoli = parameters.get("ecoli")
        nitrate = parameters.get("nitrate")

        # Rule 3 — Confirmed microbial contamination indicator (highest priority)
        # Treat any value > 0 as positive presence indicator.
        if ecoli is not None and ecoli > 0:
            return RiskResult(
                risk_level="ACTION",
                message="Microbial contamination indicator detected (E.coli present).",
                trigger_parameters=("ecoli",),
            )

        # Rule 1 — Possible microbial contamination
        # High turbidity + low disinfectant residual can indicate elevated microbial risk.
        if turbidity is not None and chlorine is not None:
            if turbidity > 5 and chlorine < 0.2:
                return RiskResult(
                    risk_level="ACTION",
                    message="Possible microbial contamination: high turbidity with low disinfectant residual.",
                    trigger_parameters=("turbidity", "chlorine"),
                )

        # Rule 2 — Pipe corrosion risk
        # Low pH + elevated lead may indicate corrosion releasing metals.
        if ph is not None and lead is not None:
            if ph < 6.5 and lead > 0.01:
                return RiskResult(
                    risk_level="ACTION",
                    message="Possible pipe corrosion releasing heavy metals (low pH with elevated lead).",
                    trigger_parameters=("ph", "lead"),
                )

        # Rule 4 — Agricultural contamination risk
        # Nitrate above 10 mg/L (as N) is a common screening threshold.
        if nitrate is not None and nitrate > 10:
            return RiskResult(
                risk_level="NOTICE",
                message="Elevated nitrate levels detected; agricultural runoff or fertilizer contamination possible.",
                trigger_parameters=("nitrate",),
            )

        return None