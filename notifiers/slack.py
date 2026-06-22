"""Slack notifier — sends Block Kit formatted alerts via Slack webhook.

Setup:
  1. https://api.slack.com/apps → Create New App → From Scratch
  2. Incoming Webhooks → Activate → Add to Workspace → Copy URL
  3. Set environment variable:
     SERVERGUARD_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

Config block:
  [[notifiers]]
  type    = "slack"
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

_SEVERITY_EMOJI = {
    "critical": ":red_circle:",
    "warning": ":large_yellow_circle:",
    "info": ":large_green_circle:",
}


class SlackNotifier(Notifier):
    """Delivers Block Kit formatted alerts to a Slack channel."""

    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    @classmethod
    def from_config(cls, block: dict) -> SlackNotifier:
        url = os.environ.get("SERVERGUARD_SLACK_WEBHOOK_URL", "")
        if not url:
            raise ValueError("SERVERGUARD_SLACK_WEBHOOK_URL env var not set")
        return cls(url)

    @property
    def name(self) -> str:
        return "slack"

    async def send(self, event: Event) -> None:
        emoji = _SEVERITY_EMOJI.get(event.severity.lower(), ":white_circle:")
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "🛡️ ServerGuard Alert"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type:*\n`{event.type}`"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{emoji} {event.severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Subject:*\n`{event.subject}`"},
                    {"type": "mrkdwn", "text": f"*Source:*\n{event.source}"},
                ],
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Message:*\n{event.message}"}},
        ]

        try:
            meta = json.loads(event.metadata_json or "{}")
            if ai_summary := meta.get("ai_summary"):
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"🤖 *AI Analysis:*\n{ai_summary}"},
                    }
                )
            if ip_ctx := meta.get("ip_context"):
                geo = (
                    f"{ip_ctx.get('city', '?')}, {ip_ctx.get('country', '?')} "
                    f"— {ip_ctx.get('isp', '?')}"
                )
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"🌍 *IP Location:*\n{geo}"},
                    }
                )
        except Exception:  # noqa: BLE001
            pass

        blocks.append({"type": "divider"})

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.post(self._webhook_url, json={"blocks": blocks})
                if resp.status_code != 200:
                    logger.warning("Slack send failed: HTTP %s", resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Slack notifier error: %s", exc)
