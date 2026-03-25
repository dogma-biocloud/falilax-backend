from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.alert_subscription import AlertSubscription
from app.services.alert_service import create_or_upsert_alert


def _alert_scope_candidates(alert: Alert) -> List[Tuple[str, str]]:
    """
    Ordered from most specific to broadest.

    household -> site -> cluster -> region -> county -> state -> country
    """
    candidates: List[Tuple[str, str]] = []

    # third layer: specific household / apt / room / site code if you later store it
    if getattr(alert, "plus_code", None):
        candidates.append(("household", str(alert.plus_code)))

    # specific named place
    if getattr(alert, "location_label", None):
        candidates.append(("site", str(alert.location_label)))

    # geo hierarchy
    if getattr(alert, "cluster_code", None):
        candidates.append(("cluster", str(alert.cluster_code)))

    if getattr(alert, "region_code", None):
        candidates.append(("region", str(alert.region_code)))

    if getattr(alert, "county_code", None):
        candidates.append(("county", str(getattr(alert, "county_code"))))

    if getattr(alert, "state_region", None):
        candidates.append(("state", str(getattr(alert, "state_region"))))

    if getattr(alert, "country", None):
        candidates.append(("country", str(getattr(alert, "country"))))

    return candidates


class AlertRoutingService:
    """
    Finds all subscribers that should receive a given alert
    based on geographic scope.
    """

    def __init__(self, db: Session):
        self.db = db

    def find_subscribers(self, alert: Alert) -> list[AlertSubscription]:
        """
        Returns matching enabled subscriptions across all valid scope levels.
        Dedupes repeated subscribers/channels/recipients if they match at multiple levels.
        """
        matched: list[AlertSubscription] = []
        seen: set[tuple[int | None, str, str | None]] = set()

        for scope_type, scope_code in _alert_scope_candidates(alert):
            stmt = (
                select(AlertSubscription)
                .where(AlertSubscription.is_enabled.is_(True))
                .where(AlertSubscription.scope_type == scope_type)
                .where(AlertSubscription.scope_code == scope_code)
            )

            subs = self.db.execute(stmt).scalars().all()

            for sub in subs:
                dedupe_key = (
                    getattr(sub, "subscriber_id", None),
                    str(getattr(sub, "delivery_channel", "in_app") or "in_app"),
                    getattr(sub, "recipient", None),
                )
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                matched.append(sub)

        return matched


def route_alert_to_subscribers(db: Session, alert: Alert) -> int:
    """
    Creates routed alert copies for all matching subscribers.

    Uses create_or_upsert_alert(), so if the same subscriber already has the
    same dedupe key, occurrence_count will increase instead of inserting duplicates.

    Also prevents routing the alert straight back to the same delivery target.
    """
    created = 0

    routing = AlertRoutingService(db)
    subs = routing.find_subscribers(alert)

    source_user_id = getattr(alert, "user_id", None)
    source_delivery_channel = str(getattr(alert, "delivery_channel", "in_app") or "in_app")
    source_recipient = getattr(alert, "recipient", None)

    for sub in subs:
        if sub.subscriber_id is None:
            continue

        target_delivery_channel = str(getattr(sub, "delivery_channel", "in_app") or "in_app")
        target_recipient = getattr(sub, "recipient", None)

        # Prevent routing the same alert right back to the same target
        if (
            int(sub.subscriber_id) == int(source_user_id or 0)
            and target_delivery_channel == source_delivery_channel
            and target_recipient == source_recipient
        ):
            continue

        create_or_upsert_alert(
            db,
            user_id=int(sub.subscriber_id),
            scope_type=str(getattr(alert, "scope_type", "water_sample")),
            scope_id=int(getattr(alert, "scope_id", 0)),
            tier=str(getattr(alert, "tier", "NOTICE")),
            parameter_code=str(getattr(alert, "parameter_code", "unknown")),
            title=str(getattr(alert, "title", "Alert")),
            message=str(getattr(alert, "message", "")),
            status="queued",
            delivery_channel=target_delivery_channel,
            recipient=target_recipient,
            scheduled_for=None,
            origin_scope_type=str(getattr(alert, "origin_scope_type", "unknown")),
            origin_scope_id=getattr(alert, "origin_scope_id", None),
            cluster_code=getattr(alert, "cluster_code", None),
            region_code=getattr(alert, "region_code", None),
            county_code=getattr(alert, "county_code", None),
            confidence=str(getattr(alert, "confidence", "suspected")),
            disclaimer=getattr(alert, "disclaimer", None),
            measured_value=getattr(alert, "measured_value", None),
            unit=getattr(alert, "unit", None),
            threshold=getattr(alert, "threshold", None),
            threshold_kind=getattr(alert, "threshold_kind", None),
            location_label=getattr(alert, "location_label", None),
            address_line1=getattr(alert, "address_line1", None),
            address_line2=getattr(alert, "address_line2", None),
            city=getattr(alert, "city", None),
            state_region=getattr(alert, "state_region", None),
            postal_code=getattr(alert, "postal_code", None),
            country=getattr(alert, "country", None),
            latitude=getattr(alert, "latitude", None),
            longitude=getattr(alert, "longitude", None),
            plus_code=getattr(alert, "plus_code", None),
            landmark=getattr(alert, "landmark", None),
            directions_hint=getattr(alert, "directions_hint", None),
        )
        created += 1

    return created