from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.alert_delivery_log import AlertDeliveryLog
from app.services.alert_message_formatter import (
    build_email_alert_message,
    build_sms_alert_message,
    build_whatsapp_alert_message,
)
from app.services.community_alert_escalation_service import (
    evaluate_community_alert_escalation,
)
from app.services.email_delivery_service import send_email
from app.services.twilio_delivery_service import send_sms


def choose_channels(
    *,
    escalation_level: str,
    recipient: dict[str, Any],
) -> list[str]:
    channels: list[str] = []

    if escalation_level in {"household_only", "site_only"}:
        channels.extend(["email", "sms"])

    if escalation_level in {"distribution_line_alert", "central_system_alert"}:
        channels.extend(["email", "sms"])

    if escalation_level == "regional_emergency":
        channels.extend(["email", "sms", "whatsapp"])

    if not channels:
        channels.append("email")

    return list(dict.fromkeys(channels))


def _split_targets(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_notification_payload(
    *,
    parameter_code: str,
    escalation_level: str,
    message: str,
    recipient: dict[str, Any],
    channel: str,
    confidence: int | float = 40,
) -> dict[str, Any]:
    location_name = recipient.get("name") or f"location:{recipient.get('location_id')}"
    parameter_name = parameter_code.upper()

    if channel == "email":
        to_target = recipient.get("email") or location_name
        formatted = build_email_alert_message(
            parameter_name=parameter_name,
            location_name=location_name,
            escalation_level=escalation_level,
            confidence=confidence,
        )
        subject = formatted["subject"]
        body = formatted["body"]

    elif channel == "sms":
        to_target = recipient.get("phone") or location_name
        subject = f"FalilaX Alert: {parameter_name}"
        body = build_sms_alert_message(
            parameter_name=parameter_name,
            location_name=location_name,
            escalation_level=escalation_level,
            confidence=confidence,
        )

    elif channel == "whatsapp":
        to_target = recipient.get("phone") or location_name
        subject = f"FalilaX Alert: {parameter_name}"
        body = build_whatsapp_alert_message(
            parameter_name=parameter_name,
            location_name=location_name,
            escalation_level=escalation_level,
            confidence=confidence,
        )

    else:
        to_target = location_name
        subject = f"FalilaX Alert: {parameter_name}"
        body = message

    return {
        "channel": channel,
        "to": to_target,
        "subject": subject,
        "body": body,
        "recipient": recipient,
    }


def persist_delivery_log(
    db: Session,
    *,
    location_id: int | None,
    parameter_code: str,
    escalation_level: str,
    payload: dict[str, Any],
    delivery_status: str = "queued",
    error_message: str | None = None,
) -> AlertDeliveryLog:
    log = AlertDeliveryLog(
        location_id=location_id,
        parameter_code=parameter_code,
        escalation_level=escalation_level,
        channel=payload.get("channel", "unknown"),
        recipient_target=str(payload.get("to", "unknown")),
        delivery_status=delivery_status,
        subject=payload.get("subject"),
        body=payload.get("body"),
        error_message=error_message,
    )
    db.add(log)
    db.flush()
    return log


def dispatch_notifications(
    db: Session,
    *,
    recipient_resolution: dict[str, Any],
    parameter_code: str,
    escalation_level: str,
    message: str,
    confidence: int | float = 40,
) -> dict[str, Any]:
    recipients = recipient_resolution.get("recipients", [])
    notifications: list[dict[str, Any]] = []
    delivery_logs: list[dict[str, Any]] = []

    for recipient in recipients:
        channels = choose_channels(
            escalation_level=escalation_level,
            recipient=recipient,
        )

        for channel in channels:
            payload = build_notification_payload(
                parameter_code=parameter_code,
                escalation_level=escalation_level,
                message=message,
                recipient=recipient,
                channel=channel,
                confidence=confidence,
            )

            if channel == "email":
                targets = _split_targets(recipient.get("email"))
                if not targets:
                    targets = [payload["to"]]

            elif channel == "sms":
                targets = _split_targets(recipient.get("phone"))
                if not targets:
                    targets = [payload["to"]]

            elif channel == "whatsapp":
                targets = _split_targets(recipient.get("phone"))
                if not targets:
                    targets = [payload["to"]]

            else:
                targets = [payload["to"]]

            targets = list(dict.fromkeys(targets))

            for target in targets:
                target_payload = {
                    **payload,
                    "to": target,
                }
                notifications.append(target_payload)

                log = persist_delivery_log(
                    db,
                    location_id=recipient.get("location_id"),
                    parameter_code=parameter_code,
                    escalation_level=escalation_level,
                    payload=target_payload,
                    delivery_status="queued",
                )

                try:
                    if channel == "email":
                        send_email(
                            to_email=target,
                            subject=target_payload["subject"],
                            body=target_payload["body"],
                        )
                        log.delivery_status = "sent"
                        log.sent_at = datetime.now(timezone.utc)

                    elif channel == "sms":
                        result = send_sms(
                            to_phone=target,
                            body=target_payload["body"],
                        )
                        log.delivery_status = result["status"]
                        log.sent_at = datetime.now(timezone.utc)

                    elif channel == "whatsapp":
                        log.delivery_status = "queued"

                    else:
                        log.delivery_status = "queued"

                except Exception as exc:
                    log.delivery_status = "failed"
                    log.error_message = str(exc)

                db.flush()

                delivery_logs.append(
                    {
                        "id": log.id,
                        "channel": log.channel,
                        "recipient_target": log.recipient_target,
                        "delivery_status": log.delivery_status,
                        "sent_at": log.sent_at.isoformat() if getattr(log, "sent_at", None) else None,
                        "error_message": log.error_message,
                    }
                )

    db.commit()

    return {
        "dispatched": len(notifications) > 0,
        "notification_count": len(notifications),
        "notifications": notifications,
        "delivery_logs": delivery_logs,
    }


def execute_alert_dispatch(
    db: Session,
    *,
    location_id: int,
    parameter_code: str,
) -> dict[str, Any]:
    escalation_result = evaluate_community_alert_escalation(
        db,
        location_id=location_id,
        parameter_code=parameter_code,
    )

    dispatch_result = dispatch_notifications(
        db,
        recipient_resolution=escalation_result.get("recipient_resolution", {}),
        parameter_code=parameter_code,
        escalation_level=escalation_result.get("escalation_level", "none"),
        message=escalation_result.get("message", ""),
        confidence=40,
    )

    return {
        "location_id": location_id,
        "parameter_code": parameter_code,
        "escalation": escalation_result,
        "dispatch": dispatch_result,
    }