from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


# -----------------------------
# 0) Shared data models
# -----------------------------

@dataclass(frozen=True)
class RiskResult:
    """
    Output of system-level multi-parameter risk evaluation.
    """
    risk_level: str  # "OK" | "NOTICE" | "ACTION"
    message: str
    trigger_parameters: tuple[str, ...]


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


@dataclass(frozen=True)
class RiskBundle:
    """
    Combined output for the caller (formatter/worker/service).
    """
    system_risk: RiskResult
    safety_guidance: SafetyGuidance
    used_parameters: tuple[str, ...]


# -----------------------------
# 1) Multi-parameter system risk
# -----------------------------

class WaterRiskEngine:
    """
    Multi-parameter risk detection engine.

    Rules are screening heuristics, not regulatory determinations.
    Output is a risk assessment signal to help escalate precautions.
    """

    # Normalize aliases -> canonical codes used across the platform
    _ALIASES = {
        "ph": "ph",

        "turbidity": "turbidity",
        "ntu": "turbidity",

        # chlorine variants (we normalize all to "chlorine")
        "chlorine": "chlorine",
        "free_chlorine": "chlorine",
        "total_chlorine": "chlorine",
        "residual_chlorine": "chlorine",
        "chlorine_residual": "chlorine",

        "lead": "lead",
        "pb": "lead",

        "ecoli": "ecoli",
        "e_coli": "ecoli",
        "total_coliform": "ecoli",  # treat as microbial indicator bucket for now

        "nitrate": "nitrate",
        "no3": "nitrate",
    }

    def _normalize(self, parameters: Dict[str, float]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k, v in (parameters or {}).items():
            if v is None:
                continue
            key = (k or "").strip().lower()
            canon = self._ALIASES.get(key)
            if not canon:
                continue
            # if multiple map to same canon, keep the "most recent" (last wins)
            out[canon] = float(v)
        return out

    def evaluate(self, parameters: Dict[str, float]) -> RiskResult:
        """
        Always returns a RiskResult (OK/NOTICE/ACTION).
        """
        p = self._normalize(parameters)

        ph = p.get("ph")
        turbidity = p.get("turbidity")
        chlorine = p.get("chlorine")
        lead = p.get("lead")
        ecoli = p.get("ecoli")
        nitrate = p.get("nitrate")

        triggered: list[str] = []
        notices: list[str] = []
        actions: list[str] = []

        # Rule A — microbial indicator detected (treat any value > 0 as positive)
        if ecoli is not None and ecoli > 0:
            actions.append("Microbial contamination indicator detected (E. coli/coliform positive).")
            triggered.append("ecoli")

        # Rule B — high turbidity + low residual chlorine (classic combined risk)
        if turbidity is not None and chlorine is not None:
            if turbidity > 5 and chlorine < 0.2:
                actions.append("Possible contamination: high turbidity with low disinfectant residual.")
                triggered.extend(["turbidity", "chlorine"])

        # Rule C — corrosion/metal release signal
        if ph is not None and lead is not None:
            if ph < 6.5 and lead > 0.01:
                actions.append("Possible corrosion/metals release: low pH with elevated lead.")
                triggered.extend(["ph", "lead"])

        # Rule D — nitrate screening
        if nitrate is not None and nitrate > 10:
            notices.append("Elevated nitrate detected; runoff/fertilizer contamination possible.")
            triggered.append("nitrate")

        # NEW Rule E — multi-parameter “system instability” signal
        # This is your requested trio: pH + turbidity + residual chlorine (chlorine)
        # If 2+ are abnormal, elevate to NOTICE; if 3 are abnormal, ACTION.
        abnormal = []
        if ph is not None and (ph < 6.5 or ph > 8.5):
            abnormal.append("ph")
        if turbidity is not None and turbidity > 5:
            abnormal.append("turbidity")
        if chlorine is not None and chlorine < 0.2:
            abnormal.append("chlorine")

        if len(abnormal) >= 3:
            actions.append("Elevated risk due to combined readings across multiple parameters.")
            triggered.extend(abnormal)
        elif len(abnormal) == 2:
            notices.append("Elevated concern: multiple parameters are outside typical range.")
            triggered.extend(abnormal)

        # De-dupe triggers while preserving order
        seen = set()
        trigger_parameters = tuple([x for x in triggered if not (x in seen or seen.add(x))])

        if actions:
            return RiskResult(
                risk_level="ACTION",
                message=" ".join(actions),
                trigger_parameters=trigger_parameters,
            )

        if notices:
            return RiskResult(
                risk_level="NOTICE",
                message=" ".join(notices),
                trigger_parameters=trigger_parameters,
            )

        return RiskResult(
            risk_level="OK",
            message="No multi-parameter risk patterns detected.",
            trigger_parameters=(),
        )


# -----------------------------
# 2) Single-parameter user-safe guidance
# -----------------------------

class WaterSafetyEngine:
    """
    Converts parameter findings into user-safe guidance.
    """

    DEFAULT_DISCLAIMER = (
        "Guidance is based on automated monitoring and may be uncertain. "
        "Confirm with certified laboratory testing and follow local public health guidance."
    )

    _RULES = {
        "ph": {
            "NOTICE": {
                "safe_for_drinking": None,
                "vulnerable": ("Infants", "Elderly", "Pregnant people"),
                "actions": (
                    "Retest soon to confirm the reading.",
                    "If taste/odor changes are present, consider avoiding drinking until confirmed by testing.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Elderly", "Pregnant people"),
                "actions": (
                    "Not recommended for drinking/cooking until pH is back in range and confirmed by retest/testing.",
                    "If this is a private source, consider treatment adjustment and retest.",
                ),
            },
        },
        "lead": {
            "NOTICE": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Pregnant people"),
                "actions": (
                    "Not recommended for drinking; use bottled/treated water.",
                    "Consider certified filtration and confirm with a certified lab test.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Pregnant people"),
                "actions": (
                    "Do not drink or cook with this water; use bottled/treated water immediately.",
                    "Confirm with a certified lab test and contact local water management if this is a public system.",
                ),
            },
        },
        "ecoli": {
            "NOTICE": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Elderly", "Immunocompromised"),
                "actions": (
                    "Not recommended for drinking; boil water or use bottled/treated water.",
                    "Confirm with lab testing and investigate contamination sources.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Children", "Elderly", "Immunocompromised"),
                "actions": (
                    "Do not drink; use bottled/treated water immediately.",
                    "Confirm with lab testing and follow provider/local authority guidance.",
                ),
            },
        },
        "turbidity": {
            "NOTICE": {
                "safe_for_drinking": None,
                "vulnerable": ("Infants", "Elderly", "Immunocompromised"),
                "actions": (
                    "Retest soon; high turbidity can reduce disinfection effectiveness.",
                    "If persistent, consider filtration and confirmatory testing.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Elderly", "Immunocompromised"),
                "actions": (
                    "Not recommended for drinking/cooking until turbidity improves and confirmed by retest/testing.",
                    "Consider filtration and follow provider guidance.",
                ),
            },
        },
        "chlorine": {
            "NOTICE": {
                "safe_for_drinking": None,
                "vulnerable": ("Infants", "Elderly", "Immunocompromised"),
                "actions": (
                    "Retest soon; low disinfectant residual can increase contamination risk.",
                    "If persistent, contact your water provider/site manager.",
                ),
            },
            "ACTION": {
                "safe_for_drinking": False,
                "vulnerable": ("Infants", "Elderly", "Immunocompromised"),
                "actions": (
                    "Increased caution advised: use bottled/treated water until confirmed by retest/testing.",
                    "Contact your water provider/site manager for guidance and confirmatory testing.",
                ),
            },
        },
    }

    def evaluate(
        self,
        *,
        parameter_code: Optional[str],
        tier: str,
        confidence: Optional[str] = None,
    ) -> SafetyGuidance:
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


# -----------------------------
# 3) Convenience: combine system + single parameter
# -----------------------------

def evaluate_with_context(
    *,
    parameters: Dict[str, float],
    parameter_code: Optional[str],
    tier: str,
    confidence: Optional[str] = None,
) -> RiskBundle:
    """
    One call for services/workers:
      - compute multi-parameter system risk
      - compute single-parameter user-safe guidance
    """
    system = WaterRiskEngine().evaluate(parameters)
    safety = WaterSafetyEngine().evaluate(parameter_code=parameter_code, tier=tier, confidence=confidence)

    used = tuple(sorted(set([*(system.trigger_parameters or ()), *(parameters or {}).keys()])))
    return RiskBundle(system_risk=system, safety_guidance=safety, used_parameters=used)