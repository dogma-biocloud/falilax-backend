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

    Priority order matters:
      1) confirmed / highest-severity hazards
      2) strong inferred hazards
      3) moderate risks
      4) mild notices

    Notes:
      - Prefer confirmed signals (e.g. E. coli presence) over inferred signals.
      - Use explicit `is not None` checks so 0.0 values are handled correctly.
      - Returns the first matching rule.
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

        # Rule 1 — Confirmed microbial contamination indicator (highest priority)
        # Any E. coli presence should be treated as critical.
        if ecoli is not None and ecoli > 0:
            return RiskResult(
                risk_level="CRITICAL",
                message="Confirmed microbial contamination indicator detected (E.coli present).",
                trigger_parameters=("ecoli",),
            )

        # Rule 2 — Severe microbial risk
        # Very high turbidity + near-zero disinfectant residual.
        if turbidity is not None and chlorine is not None:
            if turbidity > 10 and chlorine < 0.1:
                return RiskResult(
                    risk_level="CRITICAL",
                    message="Severe microbial risk: very high turbidity with critically low disinfectant residual.",
                    trigger_parameters=("turbidity", "chlorine"),
                )

        # Rule 3 — Possible microbial contamination
        if turbidity is not None and chlorine is not None:
            if turbidity > 5 and chlorine < 0.2:
                return RiskResult(
                    risk_level="ACTION",
                    message="Possible microbial contamination: high turbidity with low disinfectant residual.",
                    trigger_parameters=("turbidity", "chlorine"),
                )

        # Rule 4 — Severe corrosion / metals release risk
        if ph is not None and lead is not None:
            if ph < 6.0 and lead > 0.015:
                return RiskResult(
                    risk_level="CRITICAL",
                    message="Severe corrosion risk: strongly acidic water with elevated lead suggests metal release.",
                    trigger_parameters=("ph", "lead"),
                )

        # Rule 5 — Pipe corrosion risk
        if ph is not None and lead is not None:
            if ph < 6.5 and lead > 0.01:
                return RiskResult(
                    risk_level="ACTION",
                    message="Possible pipe corrosion releasing heavy metals (low pH with elevated lead).",
                    trigger_parameters=("ph", "lead"),
                )

        # Rule 6 — Severe nitrate contamination
        if nitrate is not None and nitrate > 20:
            return RiskResult(
                risk_level="ACTION",
                message="High nitrate levels detected; significant contamination risk is present.",
                trigger_parameters=("nitrate",),
            )

        # Rule 7 — Agricultural contamination risk
        if nitrate is not None and nitrate > 10:
            return RiskResult(
                risk_level="NOTICE",
                message="Elevated nitrate levels detected; agricultural runoff or fertilizer contamination possible.",
                trigger_parameters=("nitrate",),
            )

        # Rule 8 — Strong pH-only condition
        if ph is not None and (ph < 4.0 or ph > 10.0):
            return RiskResult(
                risk_level="CRITICAL",
                message="pH is far outside safe limits.",
                trigger_parameters=("ph",),
            )

        # Rule 9 — Mild pH-only condition
        if ph is not None and (ph < 6.5 or ph > 8.5):
            return RiskResult(
                risk_level="ACTION",
                message="pH is outside preferred water-quality limits.",
                trigger_parameters=("ph",),
            )

        return None


def evaluate_single_parameter(parameter_code: str, value: float) -> Optional[RiskResult]:
    """
    Convenience wrapper for single-parameter ingestion paths.
    Converts one reading into the multi-parameter engine format.
    """
    engine = WaterRiskEngine()
    return engine.evaluate({parameter_code.lower(): value})