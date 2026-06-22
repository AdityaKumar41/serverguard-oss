"""Notifier base class and factory.

All notifiers implement the Notifier ABC. The factory builds the active
list from config at daemon startup. If no notifiers are configured,
events are still stored — just not delivered externally.

Notifier config lives in [[notifiers]] blocks in config.toml:

  [[notifiers]]
  type    = "telegram"
  enabled = true
  # token and chat_id come from environment, NOT config file:
  # SERVERGUARD_TELEGRAM_BOT_TOKEN
  # SERVERGUARD_TELEGRAM_CHAT_ID
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from events.model import Event

logger = logging.getLogger(__name__)


class Notifier(ABC):
    """Abstract notifier — deliver a security event to an external channel."""

    @abstractmethod
    async def send(self, event: Event) -> None:
        """Send the event notification. Must not raise — log and swallow errors."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable channel name for logging."""
        ...


@dataclass
class NotifierConfig:
    """Raw config for one [[notifiers]] block."""
    type: str
    enabled: bool = True
    options: dict = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}


def build_notifiers(raw_notifier_blocks: list[dict]) -> list[Notifier]:
    """Build the list of active notifiers from config blocks."""
    from notifiers.telegram import TelegramNotifier
    from notifiers.discord import DiscordNotifier
    from notifiers.slack import SlackNotifier
    from notifiers.webhook import WebhookNotifier
    from notifiers.email import EmailNotifier

    type_map = {
        "telegram": TelegramNotifier,
        "discord": DiscordNotifier,
        "slack": SlackNotifier,
        "webhook": WebhookNotifier,
        "email": EmailNotifier,
    }

    result: list[Notifier] = []
    for block in raw_notifier_blocks:
        ntype = block.get("type", "").lower()
        enabled = bool(block.get("enabled", True))
        if not enabled:
            continue
        cls = type_map.get(ntype)
        if cls is None:
            logger.warning("Unknown notifier type: %r — skipping", ntype)
            continue
        try:
            notifier = cls.from_config(block)
            result.append(notifier)
            logger.info("Notifier registered: %s", notifier.name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to build %s notifier: %s", ntype, exc)
    return result
