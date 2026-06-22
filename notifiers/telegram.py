"""Telegram notifier — sends incident alerts via Telegram Bot API.

Setup:
  1. Create a bot: @BotFather → /newbot → copy token
  2. Get your chat ID: message the bot, then:
     curl https://api.telegram.org/bot<TOKEN>/getUpdates
  3. Set environment variables (NOT in config.toml):
     SERVERGUARD_TELEGRAM_BOT_TOKEN=123456:ABC...
     SERVERGUARD_TELEGRAM_CHAT_ID=-100123456789

Config block:
  [[notifiers]]
  type    = "telegram"
  enabled = true
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

from events.model import Event
from notifiers.base import Notifier

logger = logging.getLogger(__name__)

_SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning": "🟡",
    "info": "🟢",
}


class TelegramNotifier(Notifier):
    """Delivers alerts to a Telegram chat."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

    @classmethod
    def from_config(cls, block: dict) -> TelegramNotifier:
        token = os.environ.get("SERVERGUARD_TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("SERVERGUARD_TELEGRAM_CHAT_ID", "")
        if not token:
            raise ValueError("SERVERGUARD_TELEGRAM_BOT_TOKEN env var not set")
        if not chat_id:
            raise ValueError("SERVERGUARD_TELEGRAM_CHAT_ID env var not set")
        return cls(token, chat_id)

    @property
    def name(self) -> str:
        return "telegram"

    async def send(self, event: Event) -> None:
        emoji = _SEVERITY_EMOJI.get(event.severity.lower(), "⚪")
        text = (
            f"{emoji} *ServerGuard Alert*\n\n"
            f"*Type:* `{event.type}`\n"
            f"*Severity:* {event.severity.upper()}\n"
            f"*Source:* {event.source}\n"
            f"*Subject:* `{event.subject}`\n"
            f"*Time:* {event.timestamp}\n\n"
            f"_{event.message}_"
        )

        # Append AI summary if available
        import json
        try:
            meta = json.loads(event.metadata_json or "{}")
            if ai_summary := meta.get("ai_summary"):
                text += f"\n\n🤖 *AI Analysis:* {ai_summary}"
            if ip_ctx := meta.get("ip_context"):
                country = ip_ctx.get("country", "?")
                city = ip_ctx.get("city", "?")
                isp = ip_ctx.get("isp", "?")
                text += f"\n\n🌍 *IP Location:* {city}, {country} ({isp})"
                if ip_ctx.get("is_proxy"):
                    text += " 🔒 _[VPN/Proxy]_"
        except Exception:  # noqa: BLE001
            pass

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.post(
                    f"{self._base_url}/sendMessage",
                    json={
                        "chat_id": self._chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                )
                if not resp.json().get("ok"):
                    logger.warning("Telegram send failed: %s", resp.json().get("description"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Telegram notifier error: %s", exc)
