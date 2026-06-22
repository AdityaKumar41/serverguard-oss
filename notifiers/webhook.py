"""Generic webhook notifier — HTTP POST with HMAC-signed payload.

Setup:
  SERVERGUARD_WEBHOOK_URL=https://your-service.example.com/hook
  SERVERGUARD_WEBHOOK_SECRET=your-secret-for-hmac-verification  (optional)

Config block:
  [[notifiers]]
  type    = "webhook"
  enabled = true
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time

import httpx

from events.model import Event
from notifiers.base import Notifier

logger = logging.getLogger(__name__)


class WebhookNotifier(Notifier):
    """Delivers HMAC-signed JSON payloads to a custom HTTP endpoint."""

    def __init__(self, url: str, secret: str = "") -> None:
        self._url = url
        self._secret = secret

    @classmethod
    def from_config(cls, block: dict) -> WebhookNotifier:
        url = os.environ.get("SERVERGUARD_WEBHOOK_URL", "")
        if not url:
            raise ValueError("SERVERGUARD_WEBHOOK_URL env var not set")
        secret = os.environ.get("SERVERGUARD_WEBHOOK_SECRET", "")
        return cls(url, secret)

    @property
    def name(self) -> str:
        return "webhook"

    async def send(self, event: Event) -> None:
        payload = {
            "id": event.id,
            "timestamp": event.timestamp,
            "type": event.type,
            "severity": event.severity,
            "source": event.source,
            "subject": event.subject,
            "message": event.message,
            "metadata": json.loads(event.metadata_json or "{}"),
        }
        body = json.dumps(payload, separators=(",", ":"))

        headers = {
            "Content-Type": "application/json",
            "X-ServerGuard-Version": "0.0.1",
            "X-ServerGuard-Timestamp": str(int(time.time())),
        }

        if self._secret:
            sig = hmac.new(
                self._secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-ServerGuard-Signature"] = f"sha256={sig}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.post(self._url, content=body, headers=headers)
                if resp.status_code >= 400:
                    logger.warning("Webhook delivery failed: HTTP %s", resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Webhook notifier error: %s", exc)
