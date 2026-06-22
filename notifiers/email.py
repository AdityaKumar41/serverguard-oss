"""Email notifier — sends incident alerts via SMTP.

Setup:
  SERVERGUARD_SMTP_HOST=smtp.gmail.com
  SERVERGUARD_SMTP_PORT=587
  SERVERGUARD_SMTP_USER=alerts@example.com
  SERVERGUARD_SMTP_PASSWORD=your-app-password
  SERVERGUARD_SMTP_TO=ops@example.com

For Gmail, use an App Password (not your account password):
https://support.google.com/accounts/answer/185833

Config block:
  [[notifiers]]
  type    = "email"
  enabled = true
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from events.model import Event
from notifiers.base import Notifier

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """Delivers incident alerts via SMTP email."""

    def __init__(self, host: str, port: int, user: str, password: str, to: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._to = to

    @classmethod
    def from_config(cls, block: dict) -> EmailNotifier:
        host = os.environ.get("SERVERGUARD_SMTP_HOST", "")
        port = int(os.environ.get("SERVERGUARD_SMTP_PORT", "587"))
        user = os.environ.get("SERVERGUARD_SMTP_USER", "")
        password = os.environ.get("SERVERGUARD_SMTP_PASSWORD", "")
        to = os.environ.get("SERVERGUARD_SMTP_TO", "")
        if not host or not user or not to:
            raise ValueError("SMTP host, user, and to address required")
        return cls(host, port, user, password, to)

    @property
    def name(self) -> str:
        return "email"

    async def send(self, event: Event) -> None:
        import asyncio

        # SMTP is synchronous — run in executor to avoid blocking event loop.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._send_sync, event)

    def _send_sync(self, event: Event) -> None:
        subject = f"[ServerGuard] {event.severity.upper()}: {event.type} — {event.subject}"
        body = (
            f"ServerGuard Security Alert\n"
            f"{'=' * 50}\n\n"
            f"Event Type : {event.type}\n"
            f"Severity   : {event.severity.upper()}\n"
            f"Subject    : {event.subject}\n"
            f"Source     : {event.source}\n"
            f"Time       : {event.timestamp}\n\n"
            f"Message    : {event.message}\n"
        )

        msg = MIMEMultipart()
        msg["From"] = self._user
        msg["To"] = self._to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, self._to, msg.as_string())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Email send failed: %s", exc)
