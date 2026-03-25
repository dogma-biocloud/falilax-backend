from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.location import Location


DEFAULT_TEST_EMAIL = "dogma139@gmail.com"
DEFAULT_TEST_PHONES = "+13342200976,+17066045056,+13343545481"


def _serialize_location_recipient(
    loc: Location,
    *,
    strategy: str,
    target_label: str,
) -> dict[str, Any]:
    return {
        "type": "location",
        "location_id": loc.id,
        "name": getattr(loc, "name", None),
        "address": getattr(loc, "address", None),
        "county": getattr(loc, "county", None),
        "state": getattr(loc, "state", None),
        "central_system_id": getattr(loc, "central_system_id", None),
        "distribution_line_id": getattr(loc, "distribution_line_id", None),
        "owner_user_id": getattr(loc, "owner_user_id", None),
        "email": getattr(loc, "email", None) or DEFAULT_TEST_EMAIL,
        "phone": getattr(loc, "phone", None) or DEFAULT_TEST_PHONES,
        "target": target_label,
        "strategy": strategy,
    }


def resolve_recipients(
    db: Session,
    *,
    location_id: int,
    scope_type: str,
    scope_ids: list[int],
    strategy: str,
) -> dict[str, Any]:
    recipients: list[dict[str, Any]] = []

    if scope_type == "location":
        locations = (
            db.query(Location)
            .filter(Location.id.in_(scope_ids))
            .all()
        )

        for loc in locations:
            recipients.append(
                _serialize_location_recipient(
                    loc,
                    strategy=strategy,
                    target_label="site_admin_or_household",
                )
            )

        return {
            "resolution_level": "site",
            "recipient_count": len(recipients),
            "recipients": recipients,
            "strategy": strategy,
            "scope_ids": scope_ids,
        }

    if scope_type == "distribution_line":
        locations = (
            db.query(Location)
            .filter(Location.distribution_line_id.in_(scope_ids))
            .all()
        )

        for loc in locations:
            recipients.append(
                _serialize_location_recipient(
                    loc,
                    strategy=strategy,
                    target_label="all_locations_on_distribution_line",
                )
            )

        return {
            "resolution_level": "distribution_line",
            "recipient_count": len(recipients),
            "recipients": recipients,
            "strategy": strategy,
            "scope_ids": scope_ids,
            "note": None if recipients else "No linked locations found for distribution line scope",
        }

    if scope_type == "central_system":
        locations = (
            db.query(Location)
            .filter(Location.central_system_id.in_(scope_ids))
            .all()
        )

        for loc in locations:
            recipients.append(
                _serialize_location_recipient(
                    loc,
                    strategy=strategy,
                    target_label="all_downstream_locations_on_central_system",
                )
            )

        return {
            "resolution_level": "central_system",
            "recipient_count": len(recipients),
            "recipients": recipients,
            "strategy": strategy,
            "scope_ids": scope_ids,
            "note": None if recipients else "No linked locations found for central system scope",
        }

    if scope_type == "region":
        return {
            "resolution_level": "regional",
            "recipient_count": 0,
            "recipients": [],
            "strategy": strategy,
            "scope_ids": scope_ids,
            "note": "Regional broadcast mapping not yet implemented",
        }

    return {
        "resolution_level": "unknown",
        "recipient_count": 0,
        "recipients": [],
        "strategy": strategy,
        "scope_ids": scope_ids,
    }