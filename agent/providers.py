"""AI model provider registry — plugin-style extensibility.

Supported providers (built-in):
- openai      : OpenAI (GPT-4o, GPT-4o-mini, etc.)
- anthropic   : Anthropic (Claude 3.5 Sonnet, Claude 3 Haiku, etc.)
- openrouter  : OpenRouter (200+ models, single API key)
- ollama      : Ollama (local, free — llama3.2, mistral, gemma3, etc.)
- opencode    : OpenCode (open-source AI coding agent, OpenAI-compatible)
- groq        : Groq (ultra-fast inference — llama3, mixtral)
- mistral     : Mistral AI (mistral-large, codestral, etc.)
- together    : Together AI (open-source models, fast inference)
- disabled    : No AI features

Adding a new provider:
  1. Add to ProviderName enum
  2. Add models list to PROVIDER_MODELS
  3. Add base URL to PROVIDER_BASE_URLS
  4. Add API key env var to api_key() env_map below
  5. Add to sg setup provider picker (cli/cmd_setup.py → _PROVIDER_CHOICES)
  6. Add to .env.example

Provider config is stored in config.toml under [ai].
API keys are stored in .env (never in the TOML).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ProviderName(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    OPENCODE = "opencode"
    GROQ = "groq"
    MISTRAL = "mistral"
    TOGETHER = "together"
    DISABLED = "disabled"


# Known models per provider (first = recommended default).
# All providers use the OpenAI-compatible /chat/completions format.
PROVIDER_MODELS: dict[ProviderName, list[str]] = {
    ProviderName.OPENAI: [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ],
    ProviderName.ANTHROPIC: [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-haiku-20240307",
    ],
    ProviderName.OPENROUTER: [
        "openai/gpt-4o",
        "anthropic/claude-3-5-sonnet",
        "qwen/qwen3-235b-a22b",
        "meta-llama/llama-3.3-70b-instruct",
        "google/gemini-2.0-flash-001",
        "deepseek/deepseek-r1",
        "x-ai/grok-3-mini",
    ],
    ProviderName.OLLAMA: [
        "llama3.2",
        "mistral",
        "gemma3",
        "qwen2.5",
        "phi4",
        "deepseek-r1",
    ],
    ProviderName.OPENCODE: [
        "auto",           # OpenCode picks the best free model automatically
        "anthropic/claude-sonnet-4-5",
        "openai/gpt-4o",
    ],
    ProviderName.GROQ: [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ],
    ProviderName.MISTRAL: [
        "mistral-large-latest",
        "mistral-small-latest",
        "codestral-latest",
    ],
    ProviderName.TOGETHER: [
        "meta-llama/Llama-3-70b-chat-hf",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
    ],
    ProviderName.DISABLED: [],
}

PROVIDER_BASE_URLS: dict[ProviderName, str] = {
    ProviderName.OPENAI:      "https://api.openai.com/v1",
    ProviderName.ANTHROPIC:   "https://api.anthropic.com/v1",
    ProviderName.OPENROUTER:  "https://openrouter.ai/api/v1",
    ProviderName.OLLAMA:      "http://localhost:11434/v1",
    ProviderName.OPENCODE:    "https://api.opencode.ai/v1",
    ProviderName.GROQ:        "https://api.groq.com/openai/v1",
    ProviderName.MISTRAL:     "https://api.mistral.ai/v1",
    ProviderName.TOGETHER:    "https://api.together.xyz/v1",
    ProviderName.DISABLED:    "",
}

# Human-readable labels for the setup wizard
PROVIDER_LABELS: dict[ProviderName, str] = {
    ProviderName.OPENAI:     "OpenAI (GPT-4o, GPT-4o-mini)",
    ProviderName.ANTHROPIC:  "Anthropic (Claude 3.5 Sonnet)",
    ProviderName.OPENROUTER: "OpenRouter (200+ models, one API key)",
    ProviderName.OLLAMA:     "Ollama (local, free — llama3.2, mistral, etc.)",
    ProviderName.OPENCODE:   "OpenCode (open-source agent, free tier available)",
    ProviderName.GROQ:       "Groq (ultra-fast inference, generous free tier)",
    ProviderName.MISTRAL:    "Mistral AI (mistral-large, codestral)",
    ProviderName.TOGETHER:   "Together AI (open-source models)",
    ProviderName.DISABLED:   "Disabled — no AI features",
}

# API key env var per provider (None = no key needed)
_API_KEY_ENV: dict[ProviderName, Optional[str]] = {
    ProviderName.OPENAI:     "OPENAI_API_KEY",
    ProviderName.ANTHROPIC:  "ANTHROPIC_API_KEY",
    ProviderName.OPENROUTER: "OPENROUTER_API_KEY",
    ProviderName.OLLAMA:     None,           # local, no key
    ProviderName.OPENCODE:   "OPENCODE_API_KEY",
    ProviderName.GROQ:       "GROQ_API_KEY",
    ProviderName.MISTRAL:    "MISTRAL_API_KEY",
    ProviderName.TOGETHER:   "TOGETHER_API_KEY",
    ProviderName.DISABLED:   None,
}


@dataclass
class AIConfig:
    """AI provider configuration — loaded from config.toml [ai] section."""

    provider: ProviderName = ProviderName.DISABLED
    model: str = ""
    base_url: str = ""
    max_tokens: int = 1024
    temperature: float = 0.3

    # Plugin hook: custom provider name for non-built-in providers.
    # Set base_url + api_key_env to use any OpenAI-compatible API.
    custom_base_url: str = ""
    custom_api_key_env: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> AIConfig:
        provider_str = raw.get("provider", "disabled").lower()
        try:
            provider = ProviderName(provider_str)
        except ValueError:
            logger.warning("Unknown AI provider %r — disabling AI features", provider_str)
            provider = ProviderName.DISABLED

        model = raw.get("model", "")
        if not model and provider in PROVIDER_MODELS and PROVIDER_MODELS[provider]:
            model = PROVIDER_MODELS[provider][0]

        # Support custom base_url override (plugin pattern)
        base_url = (
            raw.get("base_url", "")
            or PROVIDER_BASE_URLS.get(provider, "")
        )

        return cls(
            provider=provider,
            model=model,
            base_url=base_url,
            max_tokens=int(raw.get("max_tokens", 1024)),
            temperature=float(raw.get("temperature", 0.3)),
            custom_base_url=raw.get("base_url", ""),
            custom_api_key_env=raw.get("api_key_env", ""),
        )

    @property
    def enabled(self) -> bool:
        return self.provider != ProviderName.DISABLED

    def api_key(self) -> Optional[str]:
        """Load the API key from environment (never from config file).

        Custom providers can specify their env var via api_key_env in config.
        """
        # Custom provider env var takes precedence
        if self.custom_api_key_env:
            return os.environ.get(self.custom_api_key_env) or None

        env_var = _API_KEY_ENV.get(self.provider)
        if env_var is None:
            return None  # Ollama / disabled

        key = os.environ.get(env_var, "")
        return key if key else None
