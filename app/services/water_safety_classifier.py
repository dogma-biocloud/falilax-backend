from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SafetyResult:
    classification: str
    guidance: str


class WaterSafetyClassifier:
    """
    Classifies water safety status using multiple parameters together.

    Output examples:
        SAFE
        CAUTION
        NOT SAFE
        BOIL WATER ADVISORY
        NOT SAFE FOR CHILDREN
    """

    def classify(self, parameters: Dict[str, float]) -> SafetyResult:

        ph = parameters.get("ph")
        turbidity = parameters.get("turbidity")
        chlorine = parameters.get("chlorine")
        lead = parameters.get("lead")
        ecoli = parameters.get("ecoli")
        nitrate = parameters.get("nitrate")

        # Highest priority — confirmed microbial contamination
        if ecoli is not None and ecoli > 0:
            return SafetyResult(
                classification="BOIL WATER ADVISORY",
                guidance="E.coli detected. Do not drink without boiling or certified treatment.",
            )

        # Possible microbial risk
        if turbidity is not None and chlorine is not None:
            if turbidity > 5 and chlorine < 0.2:
                return SafetyResult(
                    classification="NOT SAFE",
                    guidance="High turbidity with low disinfectant residual. Avoid drinking until verified safe.",
                )

        # Heavy metal risk
        if lead is not None and lead > 0.01:
            return SafetyResult(
                classification="NOT SAFE FOR CHILDREN",
                guidance="Elevated lead levels detected. Avoid use for infants and children.",
            )

        # Nitrate risk
        if nitrate is not None and nitrate > 10:
            return SafetyResult(
                classification="NOT SAFE FOR INFANTS",
                guidance="High nitrate levels detected. Unsafe for infant consumption.",
            )

        # Minor chemistry issue
        if ph is not None and (ph < 6.5 or ph > 8.5):
            return SafetyResult(
                classification="CAUTION",
                guidance="pH outside optimal range. May affect taste or corrosion potential.",
            )

        return SafetyResult(
            classification="SAFE",
            guidance="Water parameters appear within acceptable limits.",
        )