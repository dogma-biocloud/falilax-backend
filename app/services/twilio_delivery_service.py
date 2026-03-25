from __future__ import annotations

import os

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_client() -> Client:
    account_sid = _get_required_env("TWILIO_ACCOUNT_SID")
    auth_token = _get_required_env("TWILIO_AUTH_TOKEN")
    return Client(account_sid, auth_token)


def _normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if not phone.startswith("+"):
        raise ValueError("Phone number must be in E.164 format, e.g. +13342200976")
    return phone


def send_sms(
    *,
    to_phone: str,
    body: str,
) -> dict[str, str]:
    client = _get_client()
    from_phone = _get_required_env("TWILIO_SMS_FROM")
    to_phone = _normalize_phone(to_phone)

    try:
        message = client.messages.create(
            body=body,
            from_=from_phone,
            to=to_phone,
        )
        return {
            "status": message.status or "queued",
            "sid": message.sid,
            "channel": "sms",
            "to": to_phone,
        }
    except TwilioRestException as exc:
        raise RuntimeError(f"Twilio SMS send failed: {exc.msg}") from exc