from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from app.services.water_risk_engine import RiskResult, WaterRiskEngine
from app.services.water_safety_classifier import SafetyResult, WaterSafetyClassifier


@dataclass(frozen=True)
class GuidancePackage:
    risk: Optional[RiskResult]
    safety: SafetyResult

    def summary_line(self) -> str:
        # One-line “headline” safe to show users.
        if self.risk:
            return f"{self.safety.classification}: {self.risk.message}"
        return f"{self.safety.classification}: {self.safety.guidance}"


class WaterGuidanceGenerator:
    """
    Combines:
      - WaterRiskEngine (multi-parameter risk patterns)
      - WaterSafetyClassifier (user-facing safety classification)
    into a single guidance package that the alert formatter can display.
    """

    def __init__(
        self,
        *,
        risk_engine: Optional[WaterRiskEngine] = None,
        safety_classifier: Optional[WaterSafetyClassifier] = None,
    ) -> None:
        self._risk = risk_engine or WaterRiskEngine()
        self._safety = safety_classifier or WaterSafetyClassifier()

    def generate(self, parameters: Dict[str, float]) -> GuidancePackage:
        risk = self._risk.evaluate(parameters)
        safety = self._safety.classify(parameters)
        return GuidancePackage(risk=risk, safety=safety)