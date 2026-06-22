"""Telegram bot gateway for ServerGuard.

Allows ops teams to interact with a running ServerGuard daemon
directly from Telegram. Supported commands:

  /status   — show daemon status and recent event counts
  /events   — list the last 10 security events
  /ask <q>  — ask an AI question about your server's security
  /help     — show available commands

Setup:
  1. Create a bot with @BotFather
  2. Set SERVERGUARD_TELEGRAM_BOT_TOKEN
  3. Set SERVERGUARD_TELEGRAM_CHAT_ID (allows only this chat to interact)
  4. Run: sg gateway telegram --config /etc/serverguard/config.toml

The bot uses long-polling (no webhook server needed).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_POLL_TIMEOUT = 30  # seconds for long-polling
_ALLOWED_UPDATES = ["message"]


class TelegramBot:
    """Long-polling Telegram bot for ServerGuard."""

    def __init__(
        self,
        token: str,
        allowed_chat_id: str,
        store,  # storage.sqlite.Store
        ai_cfg=None,  # agent.providers.AIConfig
    ) -> None:
        self._token = token
        self._allowed_chat_id = str(allowed_chat_id)
        self._store = store
        self._ai_cfg = ai_cfg
        self._base = f"https://api.telegram.org/bot{token}"
        self._offset: int = 0
        self._running = False

    async def run(self, stop_event: asyncio.Event) -> None:
        """Poll for updates until stop_event is set."""
        self._running = True
        logger.info("[gateway/telegram] Bot started, polling for updates...")
        while not stop_event.is_set():
            try:
                updates = await self._poll()
                for update in updates:
                    await self._handle(update)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("[gateway/telegram] Poll error: %s", exc)
                await asyncio.sleep(5)
        logger.info("[gateway/telegram] Bot stopped")

    async def _poll(self) -> list:
        params = {
            "offset": self._offset,
            "timeout": _POLL_TIMEOUT,
            "allowed_updates": json.dumps(_ALLOWED_UPDATES),
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(_POLL_TIMEOUT + 5)) as client:
            resp = await client.get(f"{self._base}/getUpdates", params=params)
            data = resp.json()
            if not data.get("ok"):
                return []
            updates = data.get("result", [])
            if updates:
                self._offset = updates[-1]["update_id"] + 1
            return updates

    async def _handle(self, update: dict) -> None:
        message = update.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        # Security: only respond to the configured chat.
        if chat_id != self._allowed_chat_id:
            logger.warning("[gateway/telegram] Ignoring message from unauthorized chat %s", chat_id)
            return

        if text.startswith("/status"):
            reply = await self._cmd_status()
        elif text.startswith("/events"):
            reply = await self._cmd_events()
        elif text.startswith("/ask "):
            question = text[5:].strip()
            reply = await self._cmd_ask(question)
        elif text.startswith("/help"):
            reply = self._cmd_help()
        else:
            reply = "Unknown command. Type /help for available commands."

        await self._reply(chat_id, reply)

    async def _cmd_status(self) -> str:
        try:
            events = await self._store.list_events(limit=100)
            total = len(events)
            warnings = sum(1 for e in events if e.severity.lower() == "warning")
            critical = sum(1 for e in events if e.severity.lower() == "critical")
            return (
                f"🛡️ *ServerGuard Status*\n\n"
                f"Total events: {total}\n"
                f"⚠️ Warnings: {warnings}\n"
                f"🔴 Critical: {critical}\n\n"
                f"Daemon is running ✅"
            )
        except Exception as exc:  # noqa: BLE001
            return f"❌ Error fetching status: {exc}"

    async def _cmd_events(self) -> str:
        try:
            events = await self._store.list_events(limit=5)
            if not events:
                return "✅ No security events recorded yet."
            lines = ["📋 *Recent Events:*\n"]
            for e in events:
                emoji = "🔴" if e.severity.lower() == "critical" else "🟡"
                lines.append(f"{emoji} `{e.type}` — {e.subject}\n  _{e.message}_\n")
            return "\n".join(lines)
        except Exception as exc:  # noqa: BLE001
            return f"❌ Error: {exc}"

    async def _cmd_ask(self, question: str) -> str:
        if not self._ai_cfg or not self._ai_cfg.enabled:
            return "❌ AI is not configured. Run `sg setup` to connect an AI provider."
        from agent.client import chat
        try:
            events = await self._store.list_events(limit=20)
            context = "\n".join(f"- [{e.timestamp}] {e.type}: {e.subject} — {e.message}" for e in events)
            system = "You are a security assistant for a Linux server. Answer questions about security events concisely."
            user_msg = f"Recent events:\n{context}\n\nQuestion: {question}"
            answer = await chat(self._ai_cfg, system, user_msg)
            return f"🤖 {answer or 'No response from AI.'}"
        except Exception as exc:  # noqa: BLE001
            return f"❌ AI error: {exc}"

    def _cmd_help(self) -> str:
        return (
            "🛡️ *ServerGuard Bot Commands*\n\n"
            "/status — daemon status and event summary\n"
            "/events — last 5 security events\n"
            "/ask <question> — ask AI about your server security\n"
            "/help — show this message"
        )

    async def _reply(self, chat_id: str, text: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                await client.post(
                    f"{self._base}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gateway/telegram] Reply failed: %s", exc)
