from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FormattedAlert:
    title: str
    body: str


class AlertFormatter:
    """
    Formats alerts into human-readable messages.

    Supports:
    - parameter alerts
    - Alabama default location
    - cluster / region / county context
    - infrastructure source attribution
    - GPS navigation links
    """

    def format(
        self,
        *,
        tier: str,
        parameter_code: Optional[str] = None,
        message: Optional[str] = None,
        confidence: str = "suspected",

        measured_value: Optional[float] = None,
        unit: Optional[str] = None,
        threshold: Optional[float] = None,
        threshold_kind: Optional[str] = None,

        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state_region: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,

        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        plus_code: Optional[str] = None,
        landmark: Optional[str] = None,
        directions_hint: Optional[str] = None,

        location_label: Optional[str] = None,

        scope_type: Optional[str] = None,
        scope_id: Optional[int] = None,

        origin_scope_type: Optional[str] = None,
        origin_scope_id: Optional[int] = None,

        cluster_code: Optional[str] = None,
        region_code: Optional[str] = None,
        county_code: Optional[str] = None,

        risk_result=None,
    ) -> FormattedAlert:

        tier = tier.upper()

        # ---------------------------
        # Title
        # ---------------------------

        parameter_display = (parameter_code or "unknown").upper()

        if message:
            title = f"{tier}: {parameter_display}"
            headline = message
        else:
            title = f"{tier}: {parameter_display}"
            headline = f"{parameter_display} level requires attention"

        lines: list[str] = []
        lines.append(headline)

        # ---------------------------
        # Target
        # ---------------------------

        if scope_type and scope_id:
            lines.append("")
            lines.append(f"Target: {scope_type} #{scope_id}")

        # ---------------------------
        # Source attribution
        # ---------------------------

        if origin_scope_type:
            if origin_scope_id:
                lines.append(f"Source: {origin_scope_type} #{origin_scope_id}")
            else:
                lines.append(f"Source: {origin_scope_type}")
        else:
            lines.append("Source: unknown")

        # ---------------------------
        # Cluster / region
        # ---------------------------

        if cluster_code:
            lines.append(f"Cluster: {cluster_code}")

        if region_code:
            lines.append(f"Region: {region_code}")

        if county_code:
            lines.append(f"County: {county_code}")

        # ---------------------------
        # Location
        # ---------------------------

        location_parts = []

        if address_line1:
            location_parts.append(address_line1)

        if address_line2:
            location_parts.append(address_line2)

        if city:
            location_parts.append(city)

        if state_region:
            location_parts.append(state_region)

        if postal_code:
            location_parts.append(postal_code)

        if country:
            location_parts.append(country)

        location_string = ", ".join(location_parts)

        if not location_string:
            if location_label:
                location_string = location_label
            else:
                location_string = "AL, USA"

        lines.append("")
        lines.append(f"Location: {location_string}")

        # ---------------------------
        # GPS
        # ---------------------------

        if latitude and longitude:
            lines.append(f"GPS: {latitude}, {longitude}")
            lines.append(
                f"Navigate: https://maps.google.com/?q={latitude},{longitude}"
            )
        else:
            lines.append("GPS: Unavailable")

        # ---------------------------
        # Measurement context
        # ---------------------------

        if measured_value is not None:
            value_line = f"Measured value: {measured_value}"

            if unit:
                value_line += f" {unit}"

            lines.append("")
            lines.append(value_line)

        if threshold is not None:
            threshold_line = f"Threshold: {threshold}"

            if threshold_kind:
                threshold_line += f" ({threshold_kind})"

            lines.append(threshold_line)

        # ---------------------------
        # Drinking guidance
        # ---------------------------

        if tier == "ACTION":
            lines.append("")
            lines.append(
                "Drinking guidance: Not recommended for drinking/cooking until verified safe."
            )

        elif tier == "NOTICE":
            lines.append("")
            lines.append(
                "Drinking guidance: Water may still be usable but should be monitored."
            )

        # ---------------------------
        # Suggested actions
        # ---------------------------

        lines.append("")
        lines.append("Suggested actions:")

        lines.append(
            "- Re-test the water sample to confirm the measurement."
        )

        if tier == "ACTION":
            lines.append(
                "- Consider using bottled or treated water until results are verified."
            )

        # ---------------------------
        # Confidence disclaimer
        # ---------------------------

        if confidence == "suspected":
            lines.append("")
            lines.append(
                "Note: This alert is based on a preliminary measurement and should be confirmed with follow-up testing."
            )

        # ---------------------------
        # Multi-parameter risk (future)
        # ---------------------------

        if risk_result:
            lines.append("")
            lines.append("System risk assessment:")
            lines.append(str(risk_result))

        body = "\n".join(lines)

        return FormattedAlert(title=title, body=body)