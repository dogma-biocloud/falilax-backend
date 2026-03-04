# app/workers/alert_delivery_worker.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.alert import Alert
from app.services.alert_formatter import AlertFormatter

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeliveryResult:
    delivered_channels: tuple[str, ...]
    skipped_channels: tuple[str, ...]


class AlertDeliveryWorker:
    """
    Production-ready delivery worker with concurrency-safe claiming + failure handling.

    Status flow:
      queued  -> sending  -> sent
                    └----> failed

    Delivery in this step:
      - formats a user-facing title/body using AlertFormatter
      - logs it as "in_app" delivery (stub)
      - marks the alert as sent
    """

    def __init__(self, db: Optional[Session] = None) -> None:
        self._db = db  # injectable for tests
        self._formatter = AlertFormatter()

    def deliver_alert(self, alert_id: int) -> DeliveryResult:
        db = self._db or SessionLocal()
        close_when_done = self._db is None

        try:
            alert = db.get(Alert, alert_id)
            if not alert:
                log.warning("Alert not found", extra={"alert_id": alert_id})
                return DeliveryResult(delivered_channels=(), skipped_channels=())

            # Idempotency: only deliver queued/sending alerts
            if getattr(alert, "status", None) not in ("queued", "sending"):
                log.info(
                    "Alert not deliverable; skipping",
                    extra={"alert_id": alert.id, "status": getattr(alert, "status", None)},
                )
                return DeliveryResult(delivered_channels=(), skipped_channels=("in_app",))

            try:
                # ---- YOUR EXACT FORMAT CALL (kept inside the method) ----
                formatted = self._formatter.format(
                    tier=str(getattr(alert, "tier", "NOTICE") or "NOTICE"),
                    parameter_code=getattr(alert, "parameter_code", None),
                    message=getattr(alert, "message", None),
                    confidence=getattr(alert, "confidence", "suspected"),

                    # measured context (if you add these columns later, it will auto-work)
                    measured_value=getattr(alert, "measured_value", None),
                    unit=getattr(alert, "unit", None),
                    threshold=getattr(alert, "threshold", None),
                    threshold_kind=getattr(alert, "threshold_kind", None),

                    # location fields
                    address_line1=getattr(alert, "address_line1", None),
                    address_line2=getattr(alert, "address_line2", None),
                    city=getattr(alert, "city", None),
                    state_region=getattr(alert, "state_region", "AL"),  # Alabama default if empty
                    postal_code=getattr(alert, "postal_code", None),
                    country=getattr(alert, "country", "USA"),  # Alabama default if empty
                    latitude=getattr(alert, "latitude", None),
                    longitude=getattr(alert, "longitude", None),
                    plus_code=getattr(alert, "plus_code", None),
                    landmark=getattr(alert, "landmark", None),
                    directions_hint=getattr(alert, "directions_hint", None),

                    # NEW: label injection if address is missing
                    location_label=getattr(alert, "location_label", None) or "Alabama Water System (approx.)",

                    # NEW: cluster/source/target context
                    scope_type=getattr(alert, "scope_type", None),
                    scope_id=getattr(alert, "scope_id", None),
                    origin_scope_type=getattr(alert, "origin_scope_type", None),
                    origin_scope_id=getattr(alert, "origin_scope_id", None),
                    cluster_code=getattr(alert, "cluster_code", None),
                    region_code=getattr(alert, "region_code", None),
                    county_code=getattr(alert, "county_code", None),

                    # OPTIONAL (leave None for now until we wire multi-parameter engine)
                    risk_result=None,
                )
                # --------------------------------------------------------

                # Persist formatted title/message back onto alert if fields exist
                if hasattr(alert, "title"):
                    try:
                        alert.title = formatted.title
                    except Exception:
                        pass

                if hasattr(alert, "message"):
                    try:
                        alert.message = formatted.body
                    except Exception:
                        pass

                # "Deliver" (stub): log the final payload
                log.info(
                    "Delivering in-app alert",
                    extra={
                        "alert_id": alert.id,
                        "title": getattr(formatted, "title", None),
                        "tier": getattr(alert, "tier", None),
                        "scope_type": getattr(alert, "scope_type", None),
                        "scope_id": getattr(alert, "scope_id", None),
                        "parameter_code": getattr(alert, "parameter_code", None),
                        "cluster_code": getattr(alert, "cluster_code", None),
                        "region_code": getattr(alert, "region_code", None),
                        "county_code": getattr(alert, "county_code", None),
                        "origin_scope_type": getattr(alert, "origin_scope_type", None),
                        "origin_scope_id": getattr(alert, "origin_scope_id", None),
                    },
                )
                log.info("Alert body\n%s", getattr(formatted, "body", ""))

                # Mark as sent
                try:
                    alert.status = "sent"
                except Exception:
                    pass

                if hasattr(alert, "last_error"):
                    try:
                        alert.last_error = None
                    except Exception:
                        pass

                db.add(alert)
                db.commit()
                db.refresh(alert)

                return DeliveryResult(delivered_channels=("in_app",), skipped_channels=())

            except Exception as e:
                # Mark as failed so it doesn't remain stuck in "sending"
                err_text = f"{type(e).__name__}: {e}"
                log.exception("Delivery attempt failed", extra={"alert_id": getattr(alert, "id", alert_id)})

                try:
                    if hasattr(alert, "status"):
                        alert.status = "failed"
                    if hasattr(alert, "last_error"):
                        alert.last_error = err_text[:2000]
                    db.add(alert)
                    db.commit()
                except Exception:
                    db.rollback()
                    log.exception(
                        "Failed to mark alert as failed after delivery exception",
                        extra={"alert_id": getattr(alert, "id", alert_id)},
                    )

                raise

        except Exception:
            db.rollback()
            raise

        finally:
            if close_when_done:
                db.close()

    def deliver_pending(self, limit: int = 50) -> int:
        """
        Deliver up to `limit` queued alerts safely (concurrency-safe).

        Steps:
          1) Lock + claim queued rows (FOR UPDATE SKIP LOCKED) and set status="sending"
          2) Commit the claim
          3) Deliver each claimed alert:
               - success => sent
               - failure => failed (+ last_error if available)
        """
        db = self._db or SessionLocal()
        close_when_done = self._db is None

        try:
            q = (
                select(Alert)
                .where(Alert.status == "queued")
                .order_by(Alert.id.asc())
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
            claimed_alerts = [row[0] for row in db.execute(q).all()]

            if not claimed_alerts:
                return 0

            for a in claimed_alerts:
                try:
                    a.status = "sending"
                except Exception:
                    pass
                db.add(a)

            db.commit()

            for a in claimed_alerts:
                try:
                    self.deliver_alert(int(a.id))
                except Exception:
                    # continue delivering others
                    continue

            return len(claimed_alerts)

        except Exception:
            db.rollback()
            log.exception("deliver_pending failed")
            raise

        finally:
            if close_when_done:
                db.close()