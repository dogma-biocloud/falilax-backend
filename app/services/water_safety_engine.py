from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


# -----------------------------
# 1) Multi-parameter system risk
# -----------------------------

@dataclass(frozen=True)
class RiskResult:
    """
    Output of system-level multi-parameter risk evaluation.
    """
    risk_level: str  # "OK" | "NOTICE" | "ACTION"
    message: str
    trigger_parameters: tuple[str, ...]


class WaterRiskEngine:
    """
    Multi-parameter risk detection engine.

    This analyzes combinations of water quality parameters to detect higher-level
    risks (e.g. microbial contamination, corrosion, agricultural contamination).

    IMPORTANT:
      - Rules here are screening heuristics, not regulatory determinations.
      - Output should be treated as "risk assessment", not absolute safety verdict.
    """

    def evaluate(self, parameters: Dict[str, float]) -> Optional[RiskResult]:
        """
        Example:
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

        # Rule A — Confirmed microbial contamination indicator
        # Treat any value > 0 as positive presence indicator.
        if ecoli is not None and ecoli > 0:
            return RiskResult(
                risk_level="ACTION",
                message="Microbial contamination indicator detected (E.coli present).",
                trigger_parameters=("ecoli",),
            )

        # Rule B — Possible microbial contamination
        # High turbidity + low disinfectant residual can indicate elevated microbial risk.
        if turbidity is not None and chlorine is not None:
            if turbidity > 5 and chlorine < 0.2:
                return RiskResult(
                    risk_level="ACTION",
                    message="Possible microbial contamination: high turbidity with low disinfectant residual.",
                    trigger_parameters=("turbidity", "chlorine"),
                )

        # Rule C — Pipe corrosion risk
        # Low pH + elevated lead may indicate corrosion releasing metals.
        if ph is not None and lead is not None:
            if ph < 6.5 and lead > 0.01:
                return RiskResult(
                    risk_level="ACTION",
                    message="Possible pipe corrosion releasing heavy metals (low pH with elevated lead).",
                    trigger_parameters=("ph", "lead"),
                )

        # Rule D — Agricultural contamination risk
        # Nitrate above 10 mg/L (as N) is a common screening threshold.
        if nitrate is not None and nitrate > 10:
            return RiskResult(
                risk_level="NOTICE",
                message="Elevated nitrate levels detected; agricultural runoff or fertilizer contamination possible.",
                trigger_parameters=("nitrate",),
            )

        return None


# -----------------------------
# 2) Single-parameter user-safe guidance
# -----------------------------

@dataclass(frozen=True)
class SafetyGuidance:
    """
    What we tell the user (carefully), plus internal flags for downstream UI/logic.
    """
    risk_level: str  # "OK" | "NOTICE" | "ACTION"
    safe_for_drinking: Optional[bool]  # None if unknown/insufficient data
    vulnerable_groups: tuple[str, ...]
    suggested_actions: tuple[str, ...]
    disclaimer: str


class WaterSafetyEngine:
    """
    Converts parameter findings into user-safe guidance.

    Design goals:
      - Avoid absolute medical/legal claims.
      - Prefer "recommended / not recommended" wording.
      - Always include a disclaimer.
      - Works for any parameter via a simple rule map.
    """

    DEFAULT_DISCLAIMER = (
        "Guidance is based on automated monitoring and may be uncertain. "
        "Confirm with certified laboratory testing and follow local public health guidance."
    )

    # Minimal starter rules (we will expand this list to cover ALL parameters)
    _RULES = {
        "ph": {
            "NOTICE": {
                "safe_for_drinking": None,
                "vulnerable": ("Infants", "Elderly", "Pregnant people"),
                "actions": (
                    "If taste/odor changes are present, avoid drinking until confirmed by testing.",
                    "Use bottled/treated water for infant formula if unsure.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Elderly", "Pregnant people"),
                "actions": (
                    "Not recommended for drinking until pH is back in range and confirmed by testing.",
                    "If this is a private source, consider a treatment/neutralization system and retest.",
                ),
            },
        },
        "lead": {
            "NOTICE": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Pregnant people"),
                "actions": (
                    "Not recommended for drinking; use bottled/treated water.",
                    "Flush taps before use and consider certified filtration.",
                    "Confirm with a certified lab test and inspect plumbing sources.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Pregnant people"),
                "actions": (
                    "Do not drink or cook with this water; use bottled/treated water immediately.",
                    "Use certified filtration and confirm with a certified lab test.",
                    "Contact local water authority/management if this is a public system.",
                ),
            },
        },
        "ecoli": {
            "NOTICE": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Elderly", "Immunocompromised"),
                "actions": (
                    "Not recommended for drinking; boil water or use bottled/treated water.",
                    "Avoid using for brushing teeth unless boiled/treated.",
                    "Confirm with lab testing; investigate contamination sources.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Elderly", "Immunocompromised"),
                "actions": (
                    "Do not drink; use bottled/treated water immediately.",
                    "Boil advisory: bring to a rolling boil for at least 1 minute (if applicable).",
                    "Confirm with lab testing and sanitize/inspect storage and distribution.",
                ),
            },
        },
    }

    def evaluate(
        self,
        *,
        parameter_code: Optional[str],
        tier: str,
        confidence: Optional[str] = None,  # e.g. "suspected" | "confirmed"
    ) -> SafetyGuidance:
        """
        Inputs:
          - parameter_code: e.g. "ph", "lead", "ecoli"
          - tier: "NOTICE" or "ACTION" (we can also accept "OK")
          - confidence: optional; can slightly soften language in UI later
        """
        p = (parameter_code or "").strip().lower()
        t = (tier or "").strip().upper()

        if t not in ("OK", "NOTICE", "ACTION"):
            t = "NOTICE"

        if t == "OK":
            return SafetyGuidance(
                risk_level="OK",
                safe_for_drinking=True,
                vulnerable_groups=(),
                suggested_actions=("No action needed. Continue routine monitoring.",),
                disclaimer=self.DEFAULT_DISCLAIMER,
            )

        rule = self._RULES.get(p, {}).get(t)

        if not rule:
            generic_actions = (
                "If you suspect contamination, use bottled/treated water until confirmed by testing.",
                "Confirm with certified laboratory testing if the issue persists.",
            )
            return SafetyGuidance(
                risk_level=t,
                safe_for_drinking=None,
                vulnerable_groups=("Infants", "Children", "Elderly", "Pregnant people"),
                suggested_actions=generic_actions,
                disclaimer=self.DEFAULT_DISCLAIMER,
            )

        return SafetyGuidance(
            risk_level=t,
            safe_for_drinking=rule.get("safe_for_drinking"),
            vulnerable_groups=tuple(rule.get("vulnerable", ())),
            suggested_actions=tuple(rule.get("actions", ())),
            disclaimer=self.DEFAULT_DISCLAIMER,
        )