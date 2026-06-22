"""Incident enrichment — adds AI-generated summaries and IP context to events.

For each security event:
1. AI generates a plain-English summary of what happened and what to do.
2. IP reputation is checked via ip-api.com (free, no key needed).
3. Both are stored in the event metadata under 'ai_summary' and 'ip_context'.

This runs asynchronously after an event is stored — it never blocks detection.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from agent.client import chat
from agent.providers import AIConfig
from events.model import Event

logger = logging.getLogger(__name__)

_IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as,proxy,hosting"
_GEO_TIMEOUT = httpx.Timeout(5.0)

_ENRICHMENT_SYSTEM_PROMPT = """You are a senior Linux security engineer.
Analyze the security event and respond with:
1. A 1-sentence summary of what happened.
2. The likely intent of the attacker.
3. Recommended immediate action (one concrete command or setting change).

Be terse and factual. No markdown, no bullet points — plain prose only."""


async def enrich_event(event: Event, ai_cfg: AIConfig) -> dict:
    """Return enrichment metadata for the event.

    Always returns a dict (may be empty if both AI and geo fail).
    """
    metadata: dict = {}

    # Run AI summary and geo lookup concurrently.
    import asyncio
    ai_task = asyncio.create_task(_ai_summary(event, ai_cfg))
    geo_task = asyncio.create_task(_geo_lookup(event))

    ai_result, geo_result = await asyncio.gather(ai_task, geo_task, return_exceptions=True)

    if isinstance(ai_result, str):
        metadata["ai_summary"] = ai_result
    if isinstance(geo_result, dict):
        metadata["ip_context"] = geo_result

    return metadata


async def _ai_summary(event: Event, ai_cfg: AIConfig) -> Optional[str]:
    """Generate a plain-English AI summary of the event."""
    user_msg = (
        f"Event type: {event.type}\n"
        f"Severity: {event.severity}\n"
        f"Source: {event.source}\n"
        f"Subject: {event.subject}\n"
        f"Message: {event.message}\n"
        f"Metadata: {event.metadata_json}"
    )
    return await chat(ai_cfg, _ENRICHMENT_SYSTEM_PROMPT, user_msg)


async def _geo_lookup(event: Event) -> Optional[dict]:
    """Look up IP geolocation via ip-api.com (free, no key needed)."""
    subject = event.subject
    # Only attempt geo lookup if subject looks like an IP address.
    import re
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", subject):
        return None

    url = _IP_API_URL.format(ip=subject)
    try:
        async with httpx.AsyncClient(timeout=_GEO_TIMEOUT) as client:
            resp = await client.get(url)
            data = resp.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country", ""),
                    "city": data.get("city", ""),
                    "isp": data.get("isp", ""),
                    "org": data.get("org", ""),
                    "is_proxy": data.get("proxy", False),
                    "is_hosting": data.get("hosting", False),
                }
    except Exception as exc:  # noqa: BLE001
        logger.debug("Geo lookup failed for %s: %s", subject, exc)
    return None
