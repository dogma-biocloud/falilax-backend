# app/workers/alert_delivery_worker.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import app.models  # noqa: F401

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.alert import Alert
from app.services.alert_formatter import AlertFormatter
from app.services.alert_routing_service import route_alert_to_subscribers
from app.services.notification_service import NotificationService

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeliveryResult:
    delivered_channels: tuple[str, ...]
    skipped_channels: tuple[str, ...]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def escalated_tier(current_tier: str, occurrence_count: int) -> str:
    tier = (current_tier or "NOTICE").upper()

    if occurrence_count >= 5:
        return "CRITICAL"

    if occurrence_count >= 3 and tier == "NOTICE":
        return "ACTION"

    return tier


class AlertDeliveryWorker:
    def __init__(self, db: Optional[Session] = None) -> None:
        self._db = db
        self._formatter = AlertFormatter()
        self._notification_service = NotificationService()

    def _is_due(self, alert: Alert) -> bool:
        scheduled_for = getattr(alert, "scheduled_for", None)
        if scheduled_for is None:
            return True
        return scheduled_for <= utc_now()

    def recover_stuck_alerts(self, older_than_minutes: int = 5) -> int:
        """
        Reset old 'sending' alerts back to 'queued' so the worker can retry them.
        """
        db = self._db or SessionLocal()
        close_when_done = self._db is None

        try:
            cutoff = utc_now() - timedelta(minutes=older_than_minutes)

            stmt = (
                update(Alert)
                .where(Alert.status == "sending")
                .where(Alert.last_seen_at.is_not(None))
                .where(Alert.last_seen_at < cutoff)
                .values(status="queued")
            )

            result = db.execute(stmt)
            db.commit()
            recovered = int(result.rowcount or 0)

            if recovered:
                log.info("Recovered stuck alerts", extra={"recovered_count": recovered})

            return recovered
        except Exception:
            db.rollback()
            log.exception("Failed to recover stuck alerts")
            raise
        finally:
            if close_when_done:
                db.close()

    def deliver_alert(self, alert_id: int) -> DeliveryResult:
        db = self._db or SessionLocal()
        close_when_done = self._db is None

        try:
            alert = db.get(Alert, alert_id)
            if not alert:
                log.warning("Alert not found", extra={"alert_id": alert_id})
                return DeliveryResult(delivered_channels=(), skipped_channels=())

            if getattr(alert, "status", None) not in ("queued", "sending"):
                return DeliveryResult(
                    delivered_channels=(),
                    skipped_channels=((getattr(alert, "delivery_channel", "in_app") or "in_app"),),
                )

            if not self._is_due(alert):
                return DeliveryResult(
                    delivered_channels=(),
                    skipped_channels=((getattr(alert, "delivery_channel", "in_app") or "in_app"),),
                )

            try:
                current_occurrence_count = int(getattr(alert, "occurrence_count", 1) or 1)
                current_tier = str(getattr(alert, "tier", "NOTICE") or "NOTICE")
                new_tier = escalated_tier(current_tier, current_occurrence_count)

                if hasattr(alert, "tier"):
                    alert.tier = new_tier

                formatted = self._formatter.format(
                    tier=new_tier,
                    parameter_code=getattr(alert, "parameter_code", None),
                    message=getattr(alert, "message", None),
                    confidence=getattr(alert, "confidence", "suspected"),
                    measured_value=getattr(alert, "measured_value", None),
                    unit=getattr(alert, "unit", None),
                    threshold=getattr(alert, "threshold", None),
                    threshold_kind=getattr(alert, "threshold_kind", None),
                    address_line1=getattr(alert, "address_line1", None),
                    address_line2=getattr(alert, "address_line2", None),
                    city=getattr(alert, "city", None),
                    state_region=getattr(alert, "state_region", "AL"),
                    postal_code=getattr(alert, "postal_code", None),
                    country=getattr(alert, "country", "USA"),
                    latitude=getattr(alert, "latitude", None),
                    longitude=getattr(alert, "longitude", None),
                    plus_code=getattr(alert, "plus_code", None),
                    landmark=getattr(alert, "landmark", None),
                    directions_hint=getattr(alert, "directions_hint", None),
                    location_label=getattr(alert, "location_label", None) or "Alabama Water System (approx.)",
                    scope_type=getattr(alert, "scope_type", None),
                    scope_id=getattr(alert, "scope_id", None),
                    origin_scope_type=getattr(alert, "origin_scope_type", None),
                    origin_scope_id=getattr(alert, "origin_scope_id", None),
                    cluster_code=getattr(alert, "cluster_code", None),
                    region_code=getattr(alert, "region_code", None),
                    county_code=getattr(alert, "county_code", None),
                    risk_result=None,
                )

                formatted_title = getattr(formatted, "title", None) or (getattr(alert, "title", "") or "")
                formatted_body = getattr(formatted, "body", None) or (getattr(alert, "message", "") or "")

                # keep within DB column sizes
                safe_title = formatted_title[:255]
                safe_body = formatted_body[:1500]

                if hasattr(alert, "title"):
                    alert.title = safe_title

                if hasattr(alert, "message"):
                    alert.message = safe_body

                delivery_channel = (getattr(alert, "delivery_channel", "in_app") or "in_app").lower()
                formatted_recipient = getattr(alert, "recipient", None)

                log.info(
                    "Delivering alert",
                    extra={
                        "alert_id": getattr(alert, "id", alert_id),
                        "delivery_channel": delivery_channel,
                        "recipient": formatted_recipient,
                        "title": safe_title,
                        "tier": getattr(alert, "tier", None),
                        "occurrence_count": current_occurrence_count,
                    },
                )

                self._notification_service.send(
                    channel=delivery_channel,
                    title=safe_title,
                    body=safe_body,
                    recipient=formatted_recipient,
                )

                if hasattr(alert, "status"):
                    alert.status = "sent"
                if hasattr(alert, "sent_at"):
                    alert.sent_at = utc_now()
                if hasattr(alert, "last_error"):
                    alert.last_error = None
                if hasattr(alert, "last_error_at"):
                    alert.last_error_at = None

                db.add(alert)
                db.commit()
                db.refresh(alert)

                routed_count = 0
                if delivery_channel == "in_app":
                    try:
                        routed_count = route_alert_to_subscribers(db, alert)
                    except Exception:
                        log.exception(
                            "Routing failed after delivery",
                            extra={"alert_id": getattr(alert, "id", alert_id)},
                        )

                if routed_count:
                    log.info(
                        "Alert routed to subscribers",
                        extra={"alert_id": getattr(alert, "id", alert_id), "routed_count": routed_count},
                    )

                return DeliveryResult(
                    delivered_channels=(delivery_channel,),
                    skipped_channels=(),
                )

            except Exception as e:
                db.rollback()

                err_text = f"{type(e).__name__}: {e}"
                log.exception("Delivery attempt failed", extra={"alert_id": getattr(alert, "id", alert_id)})

                failed_alert = db.get(Alert, alert_id)
                if failed_alert:
                    try:
                        if hasattr(failed_alert, "status"):
                            failed_alert.status = "failed"
                        if hasattr(failed_alert, "delivery_attempts"):
                            current_attempts = getattr(failed_alert, "delivery_attempts", 0) or 0
                            failed_alert.delivery_attempts = int(current_attempts) + 1
                        if hasattr(failed_alert, "last_error"):
                            failed_alert.last_error = err_text[:2000]
                        if hasattr(failed_alert, "last_error_at"):
                            failed_alert.last_error_at = utc_now()
                        if hasattr(failed_alert, "last_seen_at"):
                            failed_alert.last_seen_at = utc_now()

                        db.add(failed_alert)
                        db.commit()
                    except Exception:
                        db.rollback()
                        log.exception(
                            "Failed to mark alert as failed",
                            extra={"alert_id": alert_id},
                        )

                raise

        except Exception:
            raise

        finally:
            if close_when_done:
                db.close()

    def deliver_pending(self, limit: int = 50) -> int:
        db = self._db or SessionLocal()
        close_when_done = self._db is None

        try:
            self.recover_stuck_alerts(older_than_minutes=5)

            now = utc_now()

            q = (
                select(Alert)
                .where(Alert.status == "queued")
                .where(or_(Alert.scheduled_for.is_(None), Alert.scheduled_for <= now))
                .order_by(Alert.id.asc())
                .with_for_update(skip_locked=True)
                .limit(limit)
            )

            claimed_alerts = [row[0] for row in db.execute(q).all()]
            if not claimed_alerts:
                return 0

            for a in claimed_alerts:
                a.status = "sending"
                if hasattr(a, "last_seen_at"):
                    a.last_seen_at = utc_now()
                db.add(a)

            db.commit()

            processed = 0
            for a in claimed_alerts:
                try:
                    self.deliver_alert(int(a.id))
                    processed += 1
                except Exception:
                    continue

            return processed

        except Exception:
            db.rollback()
            log.exception("deliver_pending failed")
            raise

        finally:
            if close_when_done:
                db.close()


def run_once(limit: int = 50) -> int:
    return AlertDeliveryWorker().deliver_pending(limit=limit)


if __name__ == "__main__":
    n = run_once(limit=50)
    print(f"Processed {n} alert(s).")