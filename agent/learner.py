"""Self-learning loop — ServerGuard improves detection from experience.

After accumulating N events of the same type, the learner:
1. Queries the AI to analyze the pattern.
2. Optionally recommends tightening detection thresholds.
3. Writes a 'learning.suggestion' event with the recommendation.
4. Stores custom detection tunings in ~/.serverguard/learned_thresholds.toml.

ServerGuard self-learning: observe → analyze → suggest → persist.
Learning runs asynchronously and never blocks the main detection loop.
Learning runs asynchronously and never blocks the main detection loop.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from agent.client import chat
from agent.providers import AIConfig
from events.model import Event

logger = logging.getLogger(__name__)

# Trigger a learning analysis after this many events of the same type.
LEARN_TRIGGER_COUNT = 10

_LEARNER_SYSTEM_PROMPT = """You are a security operations expert analyzing attack patterns.
You have been given a list of recent security events from a ServerGuard daemon.
Analyze the patterns and respond with a JSON object with these keys:
- summary: one paragraph describing the attack pattern you observe
- recommendation: one specific threshold change (e.g., lower failed_attempt_threshold from 5 to 3)
- threshold_key: the config key to change (e.g., failed_attempt_threshold)
- threshold_value: the new integer value to recommend
- confidence: low | medium | high

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""


class Learner:
    """Tracks event counts and triggers learning analysis when thresholds are met."""

    def __init__(self, ai_cfg: AIConfig, data_dir: str) -> None:
        self._ai_cfg = ai_cfg
        self._data_dir = Path(data_dir)
        self._event_buffer: dict[str, list[Event]] = {}  # type -> [event]

    async def observe(self, event: Event) -> Optional[str]:
        """Feed an event to the learner. Returns a learning summary if analysis ran."""
        if not self._ai_cfg.enabled:
            return None

        event_type = event.type
        if event_type not in self._event_buffer:
            self._event_buffer[event_type] = []
        self._event_buffer[event_type].append(event)

        if len(self._event_buffer[event_type]) >= LEARN_TRIGGER_COUNT:
            result = await self._analyze(event_type)
            self._event_buffer[event_type].clear()  # reset after analysis
            return result

        return None

    async def _analyze(self, event_type: str) -> Optional[str]:
        """Run AI analysis on accumulated events of this type."""
        events = self._event_buffer.get(event_type, [])
        if not events:
            return None

        events_text = "\n".join(
            f"- [{e.timestamp}] {e.subject}: {e.message}" for e in events
        )
        user_msg = f"Event type: {event_type}\n\nRecent events:\n{events_text}"

        logger.info("[learner] Running AI analysis on %d %s events", len(events), event_type)
        response = await chat(self._ai_cfg, _LEARNER_SYSTEM_PROMPT, user_msg)

        if not response:
            return None

        try:
            suggestion = json.loads(response)
            self._save_suggestion(event_type, suggestion)
            logger.info(
                "[learner] New suggestion for %s: %s (confidence: %s)",
                event_type,
                suggestion.get("recommendation", ""),
                suggestion.get("confidence", "unknown"),
            )
            return suggestion.get("summary", "")
        except json.JSONDecodeError:
            logger.debug("[learner] AI returned non-JSON: %s", response[:100])
            return response

    def _save_suggestion(self, event_type: str, suggestion: dict) -> None:
        """Persist the learning suggestion to disk."""
        suggestions_file = self._data_dir / "learned_suggestions.json"
        existing: list = []
        if suggestions_file.exists():
            try:
                existing = json.loads(suggestions_file.read_text())
            except Exception:  # noqa: BLE001
                existing = []

        existing.append({"event_type": event_type, **suggestion})
        suggestions_file.write_text(json.dumps(existing, indent=2))
        logger.debug("[learner] Saved suggestion to %s", suggestions_file)
