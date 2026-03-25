from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> dict:
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    mail_from = os.getenv("MAIL_FROM", username)
    server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    port = int(os.getenv("MAIL_PORT", "587"))
    use_starttls = os.getenv("MAIL_STARTTLS", "true").lower() == "true"

    if not username or not password or not mail_from:
        raise ValueError("Mail environment variables are not fully configured")

    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(server, port) as smtp:
        smtp.ehlo()
        if use_starttls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)

    return {
        "sent": True,
        "channel": "email",
        "to": to_email,
        "subject": subject,
    }