"""Discord notifier — sends rich embed alerts via Discord webhook.

Setup:
  1. Discord Server → Settings → Integrations → Webhooks → New Webhook
  2. Copy the webhook URL
  3. Set environment variable:
     SERVERGUARD_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

Config block:
  [[notifiers]]
  type    = "discord"
  enabled = true
"""

from __future__ import annotations

import json
import logging
import os

import httpx

from events.model import Event
from notifiers.base import Notifier

logger = logging.getLogger(__name__)

_SEVERITY_COLORS = {
    "critical": 0xFF0000,  # red
    "warning": 0xFF9900,   # orange
    "info": 0x00CC44,      # green
}


class DiscordNotifier(Notifier):
    """Delivers rich embed alerts to a Discord channel."""

    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    @classmethod
    def from_config(cls, block: dict) -> DiscordNotifier:
        url = os.environ.get("SERVERGUARD_DISCORD_WEBHOOK_URL", "")
        if not url:
            raise ValueError("SERVERGUARD_DISCORD_WEBHOOK_URL env var not set")
        return cls(url)

    @property
    def name(self) -> str:
        return "discord"

    async def send(self, event: Event) -> None:
        color = _SEVERITY_COLORS.get(event.severity.lower(), 0x888888)

        fields = [
            {"name": "Type", "value": f"`{event.type}`", "inline": True},
            {"name": "Severity", "value": event.severity.upper(), "inline": True},
            {"name": "Source", "value": event.source, "inline": True},
            {"name": "Subject", "value": f"`{event.subject}`", "inline": True},
            {"name": "Time", "value": event.timestamp, "inline": True},
        ]

        # Add AI summary and geo if available
        try:
            meta = json.loads(event.metadata_json or "{}")
            if ai_summary := meta.get("ai_summary"):
                fields.append({"name": "🤖 AI Analysis", "value": ai_summary, "inline": False})
            if ip_ctx := meta.get("ip_context"):
                geo = f"{ip_ctx.get('city', '?')}, {ip_ctx.get('country', '?')}"
                if ip_ctx.get("is_proxy"):
                    geo += " (VPN/Proxy)"
                fields.append({"name": "🌍 IP Location", "value": geo, "inline": True})
        except Exception:  # noqa: BLE001
            pass

        payload = {
            "username": "ServerGuard",
            "avatar_url": "https://raw.githubusercontent.com/serverguard-oss/serverguard/main/image/image.png",
            "embeds": [{
                "title": f"🛡️ Security Alert — {event.type}",
                "description": event.message,
                "color": color,
                "fields": fields,
                "footer": {"text": "ServerGuard v0.0.1"},
            }],
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.post(self._webhook_url, json=payload)
                if resp.status_code not in (200, 204):
                    logger.warning("Discord send failed: HTTP %s", resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Discord notifier error: %s", exc)
