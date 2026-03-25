from __future__ import annotations

import logging
from typing import Optional


log = logging.getLogger(__name__)


class NotificationService:
    """
    Channel dispatcher for FalilaX notifications.

    Current behavior:
      - in_app: logs delivery
      - email: validates recipient, then logs delivery
      - sms: validates recipient, then logs delivery

    Later you can plug in:
      - SendGrid / SES for email
      - Twilio for SMS
      - websocket / push for in-app real-time delivery
    """

    def send_in_app(
        self,
        *,
        title: str,
        body: str,
        recipient: Optional[str] = None,
    ) -> None:
        log.info(
            "IN_APP notification sent",
            extra={
                "recipient": recipient,
                "title": title,
                "body": body,
            },
        )

    def send_email(
        self,
        *,
        title: str,
        body: str,
        recipient: str,
    ) -> None:
        if not recipient:
            raise ValueError("Email recipient is required for email delivery")

        log.info(
            "EMAIL notification sent",
            extra={
                "recipient": recipient,
                "title": title,
                "body": body,
            },
        )

    def send_sms(
        self,
        *,
        title: str,
        body: str,
        recipient: str,
    ) -> None:
        if not recipient:
            raise ValueError("Phone recipient is required for sms delivery")

        log.info(
            "SMS notification sent",
            extra={
                "recipient": recipient,
                "title": title,
                "body": body,
            },
        )

    def send(
        self,
        *,
        channel: str,
        title: str,
        body: str,
        recipient: Optional[str] = None,
    ) -> None:
        normalized = (channel or "in_app").lower()

        if normalized == "email":
            self.send_email(title=title, body=body, recipient=str(recipient or ""))
            return

        if normalized == "sms":
            self.send_sms(title=title, body=body, recipient=str(recipient or ""))
            return

        # default
        self.send_in_app(title=title, body=body, recipient=recipient)