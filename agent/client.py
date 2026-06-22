"""Thin async HTTP client for AI model chat completions.

Uses the OpenAI-compatible API format which all supported providers
(OpenAI, Anthropic via compatibility layer, OpenRouter, Ollama) support.
This keeps the client simple and provider-agnostic.
"""

from __future__ import annotations

import logging

import httpx

from agent.providers import AIConfig

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0, connect=5.0)


async def chat(
    cfg: AIConfig,
    system_prompt: str,
    user_message: str,
) -> str | None:
    """Send one chat turn and return the assistant's reply.

    Returns None if AI is disabled or if the call fails (non-fatal).
    """
    if not cfg.enabled:
        return None

    api_key = cfg.api_key()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Anthropic via OpenRouter works with OpenAI-compat format.
    # Native Anthropic SDK not required.
    payload = {
        "model": cfg.model,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }

    url = cfg.base_url.rstrip("/") + "/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        logger.warning("AI API error %s: %s", exc.response.status_code, exc.response.text[:200])
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI call failed: %s", exc)
        return None
