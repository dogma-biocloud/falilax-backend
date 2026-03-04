from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.alert import Alert

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedAlert:
    alert_id: int
    created: bool  # False means we updated an existing alert (dedupe)


class AlertGenerator:
    """
    Alert generator with dedupe-safe behavior.

    If an alert with the same (user_id, scope_type, scope_id, tier, parameter_code)
    already exists (enforced by ux_alerts_dedupe), we update it instead of inserting:

      - occurrence_count += 1 (if column exists)
      - last_seen_at = now() (if column exists)
      - status:
          - if existing is "sent" or "sending" -> leave as-is (don't re-queue)
          - if existing is "failed" -> set back to "queued" (retry)
          - if existing is "queued" -> keep queued

    Title is required (NOT NULL), so we always provide it.
    """

    def __init__(self, db: Optional[Session] = None) -> None:
        self._db = db

    def create_or_bump_alert(
        self,
        *,
        user_id: int,
        tier: str,
        scope_type: str,
        scope_id: int,
        parameter_code: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
        origin_scope_type: str = "unknown",
        cluster_code: Optional[str] = None,
        confidence: str = "suspected",
    ) -> GeneratedAlert:
        db = self._db or SessionLocal()
        close_when_done = self._db is None

        # title is NOT NULL in your schema
        if not title:
            title = f"{tier}: {parameter_code.upper()} alert"

        now = datetime.now(timezone.utc)

        try:
            # Try insert first (fast path)
            alert = Alert(
                user_id=user_id,
                tier=tier,
                scope_type=scope_type,
                scope_id=scope_id,
                parameter_code=parameter_code,
                origin_scope_type=origin_scope_type,
                cluster_code=cluster_code,
                confidence=confidence,
                status="queued",
                title=title,
                message=message,
            )

            # If message ends up NOT NULL in schema, keep it safe
            if getattr(alert, "message", None) is None:
                try:
                    alert.message = ""
                except Exception:
                    pass

            # If columns exist, initialize them
            if hasattr(alert, "occurrence_count") and getattr(alert, "occurrence_count", None) is None:
                try:
                    alert.occurrence_count = 1
                except Exception:
                    pass

            if hasattr(alert, "last_seen_at"):
                try:
                    alert.last_seen_at = now
                except Exception:
                    pass

            db.add(alert)
            db.commit()
            db.refresh(alert)

            log.info(
                "Alert created",
                extra={
                    "alert_id": alert.id,
                    "tier": tier,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "parameter_code": parameter_code,
                },
            )
            return GeneratedAlert(alert_id=alert.id, created=True)

        except IntegrityError:
            # Duplicate detected by ux_alerts_dedupe -> update existing row
            db.rollback()

            existing = db.execute(
                select(Alert)
                .where(
                    Alert.user_id == user_id,
                    Alert.scope_type == scope_type,
                    Alert.scope_id == scope_id,
                    Alert.tier == tier,
                    Alert.parameter_code == parameter_code,
                )
                .limit(1)
            ).scalar_one_or_none()

            if not existing:
                # Extremely rare race; re-raise so we see it
                raise

            # bump counters if present
            if hasattr(existing, "occurrence_count"):
                try:
                    existing.occurrence_count = int(getattr(existing, "occurrence_count", 1) or 1) + 1
                except Exception:
                    pass

            if hasattr(existing, "last_seen_at"):
                try:
                    existing.last_seen_at = now
                except Exception:
                    pass

            # Optional: update title/message (keep latest)
            try:
                existing.title = title
            except Exception:
                pass

            if message is not None:
                try:
                    existing.message = message
                except Exception:
                    pass

            # Status handling (don’t disturb sent/sending)
            cur_status = getattr(existing, "status", None)
            if cur_status == "failed":
                existing.status = "queued"
            elif cur_status in (None, ""):
                existing.status = "queued"

            # Clear last_error on retry if column exists
            if getattr(existing, "status", None) == "queued" and hasattr(existing, "last_error"):
                try:
                    existing.last_error = None
                except Exception:
                    pass

            db.add(existing)
            db.commit()
            db.refresh(existing)

            log.info(
                "Alert deduped (bumped existing)",
                extra={
                    "alert_id": existing.id,
                    "tier": tier,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "parameter_code": parameter_code,
                    "status": getattr(existing, "status", None),
                    "occurrence_count": getattr(existing, "occurrence_count", None),
                },
            )
            return GeneratedAlert(alert_id=existing.id, created=False)

        finally:
            if close_when_done:
                db.close()