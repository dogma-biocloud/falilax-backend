from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Optional: if you pass risk_result from WaterRiskEngine
try:
    from app.services.water_risk_engine import RiskResult
except Exception:  # pragma: no cover
    RiskResult = object  # type: ignore


def _fmt_address(
    address_line1: Optional[str],
    address_line2: Optional[str],
    city: Optional[str],
    state_region: Optional[str],
    postal_code: Optional[str],
    country: Optional[str],
) -> str:
    parts: list[str] = []
    if address_line1:
        parts.append(address_line1.strip())
    if address_line2:
        parts.append(address_line2.strip())

    # Defaults for Alabama deployment
    state_region = (state_region or "AL").strip() if state_region is not None else "AL"
    country = (country or "USA").strip() if country is not None else "USA"

    city_line = ", ".join([p for p in [city, state_region] if p])
    if postal_code:
        city_line = f"{city_line} {postal_code}".strip() if city_line else postal_code

    if city_line:
        parts.append(city_line)
    if country:
        parts.append(country)

    return ", ".join([p for p in parts if p]) or "Unknown address"


def _maps_link(lat: Optional[float], lon: Optional[float]) -> Optional[str]:
    if lat is None or lon is None:
        return None
    return f"https://www.google.com/maps?q={lat},{lon}"


def _risk_actions_generic(tier: str, *, escalate: bool = False) -> list[str]:
    """
    Generic actions that are safe to recommend for ANY parameter.
    If escalate=True, nudge toward stronger precautions (still cautious wording).
    """
    t = (tier or "").upper()

    if t == "NOTICE":
        base = [
            "Monitor and retest soon to confirm the reading.",
            "If the water looks/smells unusual, avoid drinking until rechecked.",
            "If this repeats, contact your water provider or site manager.",
        ]
        if escalate:
            base.insert(
                1,
                "Because multiple signals may be involved, consider using an alternative water source until verified.",
            )
        return base

    if t == "ACTION":
        base = [
            "Precaution advised: consider using bottled or treated water for drinking and cooking until confirmed by retest.",
            "If you have a point-of-use filter certified for your concern, follow the manufacturer instructions.",
            "Contact your water provider/site manager for guidance and confirmatory testing.",
        ]
        if escalate:
            base.insert(0, "Escalated precaution advised due to multi-parameter risk assessment.")
        return base

    base = [
        "Precaution advised: retest to confirm the reading.",
        "If concerned, use an alternative water source until verified.",
        "Contact your water provider/site manager for next steps.",
    ]
    if escalate:
        base.insert(1, "If multiple parameters are abnormal, consider stronger precautions until verified.")
    return base


def _sensitive_group_note(confidence: Optional[str]) -> str:
    c = (confidence or "").lower()
    if c in ("confirmed", "high"):
        return (
            "Extra caution recommended for infants/young children, pregnant people, elderly, "
            "and immunocompromised individuals until verified safe by certified testing."
        )
    return (
        "If sensitive groups are present (infants/young children, pregnant people, elderly, immunocompromised), "
        "consider extra caution until confirmatory testing."
    )


def _disclaimer(confidence: Optional[str]) -> str:
    c = (confidence or "").lower()
    if c in ("confirmed", "high"):
        return "Guidance based on available readings and rules; follow local authority instructions for final decisions."
    return "Guidance only based on preliminary sensor readings; confirm with certified testing or local authority for final decisions."


def _parameter_hint(parameter_code: Optional[str]) -> Optional[str]:
    if not parameter_code:
        return None

    p = parameter_code.strip().lower()

    if p in ("ecoli", "e_coli", "total_coliform", "coliform"):
        return (
            "Microbial indicators can suggest contamination risk. Consider using an alternative source "
            "until confirmatory testing and guidance from your provider."
        )

    if p in ("turbidity",):
        return (
            "High turbidity can reduce disinfection effectiveness and may signal particulate contamination. "
            "Consider filtration and retesting; follow provider guidance."
        )

    if p in ("lead", "pb", "arsenic", "as", "mercury", "hg", "cadmium", "cd"):
        return (
            "Heavy metals concerns often require certified testing and appropriate treatment (e.g., certified filters). "
            "Consider alternative water for drinking/cooking until confirmed."
        )

    if p in ("nitrate", "no3", "nitrite", "no2"):
        return (
            "Nutrient contamination concerns may require certified testing. "
            "Consider extra caution for infants and follow provider/authority guidance."
        )

    if p in ("ph",):
        return (
            "Out-of-range pH may affect taste/corrosivity and can indicate treatment issues. "
            "Retest and consult your provider if persistent."
        )

    if p in ("chlorine", "free_chlorine", "total_chlorine"):
        return "Disinfectant levels outside expectations may indicate treatment changes. Retest and consult your provider for guidance."

    return None


def _drinking_guidance_line(*, tier: str, confidence: Optional[str], escalate: bool = False) -> str:
    t = (tier or "").upper()
    c = (confidence or "").lower()

    if escalate:
        return (
            "Drinking guidance: Increased caution advised due to multi-parameter risk assessment; "
            "avoid drinking/cooking until verified safe by retest or certified testing."
        )

    if t == "ACTION":
        return "Drinking guidance: Not recommended for drinking/cooking until verified safe by retest or certified testing."

    if t == "NOTICE":
        if c in ("confirmed", "high"):
            return "Drinking guidance: Use caution and follow provider guidance; verify with retest/certified testing."
        return "Drinking guidance: Use caution until verified by retest."

    return "Drinking guidance: Use caution until verified by retest or certified testing."


def _multi_parameter_note() -> str:
    return (
        "Note: Real water safety decisions depend on multiple parameters together. "
        "This alert reflects one reading/rule and should be interpreted alongside other parameters and confirmatory testing."
    )


def _system_risk_note() -> str:
    return (
        "Note: This multi-parameter assessment may indicate higher concern than a single-parameter alert. "
        "Consider escalated precautions and confirmatory testing."
    )


def _tier_rank(tier: str) -> int:
    t = (tier or "").upper()
    if t == "ACTION":
        return 2
    if t == "NOTICE":
        return 1
    return 0


def _should_escalate(single_tier: str, risk_result: Optional[RiskResult]) -> bool:
    if not risk_result:
        return False
    rr = getattr(risk_result, "risk_level", None)
    if not rr:
        return False
    return _tier_rank(str(rr)) > _tier_rank(single_tier)


def _location_line(*, location_label: Optional[str], addr: str, country: Optional[str]) -> str:
    """
    Prefer location_label whenever provided (cleaner for humans).
    Fall back to formatted address otherwise.
    """
    if location_label and location_label.strip():
        # Keep as-is; don't force extra ", USA" because label may already include it.
        return location_label.strip()

    # If addr is unknown, at least show state/country defaults from formatter
    if addr and addr != "Unknown address":
        return addr

    # Final fallback
    c = (country or "USA").strip()
    return f"Unknown address ({c})" if c else "Unknown address"


@dataclass(frozen=True)
class FormattedAlert:
    title: str
    body: str


class AlertFormatter:
    """
    Formats an Alert into a human-readable message including:
      - Alabama defaults (AL/USA)
      - location_label preferred when available
      - cluster/source/target context
      - optional system risk assessment (risk_result)
      - safe suggested actions + disclaimer
    """

    def format(
        self,
        *,
        tier: str,
        parameter_code: Optional[str],
        message: Optional[str],
        confidence: Optional[str] = "suspected",
        risk_result: Optional[RiskResult] = None,
        measured_value: Optional[float] = None,
        unit: Optional[str] = None,
        threshold: Optional[float] = None,
        threshold_kind: Optional[str] = None,
        # location
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state_region: Optional[str] = "AL",
        postal_code: Optional[str] = None,
        country: Optional[str] = "USA",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        plus_code: Optional[str] = None,
        landmark: Optional[str] = None,
        directions_hint: Optional[str] = None,
        location_label: Optional[str] = None,
        # context
        scope_type: Optional[str] = None,
        scope_id: Optional[int] = None,
        origin_scope_type: Optional[str] = None,
        origin_scope_id: Optional[int] = None,
        cluster_code: Optional[str] = None,
        region_code: Optional[str] = None,
        county_code: Optional[str] = None,
    ) -> FormattedAlert:
        single_tier = (tier or "NOTICE").upper()
        display_tier = single_tier

        # If system risk is higher, display that tier in title
        if risk_result and getattr(risk_result, "risk_level", None):
            rr = str(getattr(risk_result, "risk_level"))
            if _tier_rank(rr) > _tier_rank(single_tier):
                display_tier = rr.upper()

        title = f"{display_tier}: {parameter_code.upper() if parameter_code else 'ALERT'}"

        addr = _fmt_address(address_line1, address_line2, city, state_region, postal_code, country)
        gps = f"{latitude}, {longitude}" if (latitude is not None and longitude is not None) else "Unavailable"
        link = _maps_link(latitude, longitude)

        escalate = _should_escalate(single_tier, risk_result)

        lines: list[str] = []

        # What happened
        if message:
            lines.append(message.strip())

        # Measured context (factual)
        if measured_value is not None:
            ctx = f"Reading: {measured_value}{(' ' + unit) if unit else ''}"
            if threshold is not None:
                tk = f" ({threshold_kind})" if threshold_kind else ""
                ctx += f" | Threshold{tk}: {threshold}{(' ' + unit) if unit else ''}"
            lines.append(ctx)

        # Location block
        lines.append("")
        loc_line = _location_line(location_label=location_label, addr=addr, country=country)
        lines.append(f"Location: {loc_line}")

        if landmark:
            lines.append(f"Landmark: {landmark}")
        lines.append(f"GPS: {gps}")
        if plus_code:
            lines.append(f"Plus Code: {plus_code}")
        if directions_hint:
            lines.append(f"Directions: {directions_hint}")
        if link:
            lines.append(f"Navigate: {link}")

        # Cluster/source/target context
        ctx_bits: list[str] = []
        if scope_type and scope_id is not None:
            ctx_bits.append(f"Target: {scope_type}:{scope_id}")
        if origin_scope_type and origin_scope_id is not None:
            ctx_bits.append(f"Source: {origin_scope_type}:{origin_scope_id}")
        if cluster_code:
            ctx_bits.append(f"Cluster: {cluster_code}")
        if region_code:
            ctx_bits.append(f"Region: {region_code}")
        if county_code:
            ctx_bits.append(f"County: {county_code}")

        if ctx_bits:
            lines.append("")
            lines.append("Context:")
            for b in ctx_bits:
                lines.append(f"- {b}")

        # Drinking guidance
        lines.append("")
        lines.append(_drinking_guidance_line(tier=single_tier, confidence=confidence, escalate=escalate))

        # Multi-parameter note (always)
        lines.append("")
        lines.append(_multi_parameter_note())

        # System risk assessment block
        if risk_result:
            rr_level = getattr(risk_result, "risk_level", None)
            rr_msg = getattr(risk_result, "message", None)
            rr_triggers = getattr(risk_result, "trigger_parameters", None)

            lines.append("")
            lines.append("System risk assessment (multi-parameter):")
            if rr_level:
                lines.append(f"- Level: {rr_level}")
            if rr_msg:
                lines.append(f"- Summary: {rr_msg}")
            if rr_triggers:
                try:
                    trig = ", ".join(rr_triggers)
                except Exception:
                    trig = str(rr_triggers)
                lines.append(f"- Triggered by: {trig}")
            lines.append(f"- {_system_risk_note()}")

        # Suggested actions
        lines.append("")
        lines.append("Suggested actions:")
        for a in _risk_actions_generic(single_tier, escalate=escalate):
            lines.append(f"- {a}")

        # Parameter hint
        hint = _parameter_hint(parameter_code)
        if hint:
            lines.append("")
            lines.append(f"Note ({parameter_code.upper()}): {hint}")

        # Sensitive groups + disclaimer
        lines.append("")
        lines.append(_sensitive_group_note(confidence))
        lines.append("")
        lines.append(f"Disclaimer: {_disclaimer(confidence)}")

        body = "\n".join(lines).strip()
        return FormattedAlert(title=title, body=body)