"""sg ask — ask an AI question about your server's security history.

Queries the event database for context, then sends a natural-language
question to your configured AI provider.

Usage:
  sg ask "Why was 203.0.113.10 flagged?"
  sg ask "Summarize the last 24 hours of security events"
  sg ask "Am I under attack? What should I do?"
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

console = Console()


def run(config: str, question: str) -> None:
    """Run an AI-powered Q&A over the event database."""
    import asyncio

    asyncio.run(_run_async(config, question))


async def _run_async(config: str, question: str) -> None:
    from config.loader import load
    from storage.sqlite import Store

    try:
        cfg = load(config)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise SystemExit(1) from None

    # Load AI config
    ai_cfg = _load_ai_cfg(cfg)
    if not ai_cfg.enabled:
        console.print(
            Panel(
                "AI is not configured.\n\n"
                "Run [bold cyan]sg setup[/] to connect a model provider,\n"
                "or [bold cyan]sg model[/] to change providers.",
                title="⚠️  AI Not Configured",
                border_style="yellow",
            )
        )
        raise SystemExit(1)

    store = await Store.open(cfg.db_path)
    events = await store.list_events(limit=50)
    await store.close()

    # Build context from events
    context_lines = []
    for e in events:
        context_lines.append(
            f"[{e.timestamp}] {e.type} | severity={e.severity} | "
            f"subject={e.subject} | message={e.message}"
        )
    context = "\n".join(context_lines) if context_lines else "No events recorded yet."

    system_prompt = (
        "You are a senior Linux security engineer with deep expertise in threat analysis.\n"
        "The user is asking about their server's security. Answer directly and practically.\n"
        "Be concise. Give actionable advice. Mention specific commands when useful.\n"
        "If you don't have enough context, say so clearly."
    )
    user_msg = f"Recent security events from this server:\n{context}\n\nQuestion: {question}"

    from agent.client import chat

    console.print(f"\n[dim]🤖 Asking {ai_cfg.provider.value}/{ai_cfg.model}...[/]\n")

    answer = await chat(ai_cfg, system_prompt, user_msg)

    if answer:
        console.print(
            Panel(
                answer,
                title=f"🤖 AI Answer — {ai_cfg.provider.value}/{ai_cfg.model}",
                border_style="cyan",
            )
        )
    else:
        console.print("[red]AI returned no response. Check your API key and connection.[/]")
        raise SystemExit(1)


def _load_ai_cfg(cfg):
    # Try to load [ai] section from raw config
    import tomllib
    from pathlib import Path

    from agent.providers import AIConfig

    try:
        raw = tomllib.loads(Path(cfg.config_path).read_text())
        return AIConfig.from_dict(raw.get("ai", {}))
    except Exception:
        from agent.providers import AIConfig, ProviderName

        return AIConfig(provider=ProviderName.DISABLED)
