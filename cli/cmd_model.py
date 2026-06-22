"""sg model — switch AI model provider.

Reads and writes the [ai] section of the config file.

Reads and writes the [ai] section of the config file.

Usage:
  sg model                          # interactive picker
  sg model set openai gpt-4o
  sg model set ollama llama3.2
  sg model set anthropic claude-3-5-sonnet-20241022
  sg model set openrouter qwen/qwen3-235b-a22b
  sg model list                     # show available providers + models
"""

from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from agent.providers import PROVIDER_MODELS, PROVIDER_BASE_URLS, ProviderName

console = Console()


def run_interactive(config: str) -> None:
    """Interactive model picker."""
    _print_provider_table()
    choices = [p.value for p in ProviderName]
    provider = Prompt.ask("\nProvider", choices=choices, default="disabled")

    if provider == "disabled":
        console.print("[yellow]AI disabled.[/]")
        return

    pname = ProviderName(provider)
    models = PROVIDER_MODELS.get(pname, [])
    if models:
        console.print(f"\nAvailable models for {provider}:")
        for i, m in enumerate(models, 1):
            console.print(f"  [{i}] {m}")
        model = Prompt.ask("Model", default=models[0])
    else:
        model = Prompt.ask("Model name")

    _save_model(config, provider, model)
    console.print(f"\n[green]✅ Model set to [bold]{provider}[/] / [bold]{model}[/][/]")
    console.print("[dim]Restart sgd for changes to take effect.[/]")


def run_set(config: str, provider: str, model: str) -> None:
    """Non-interactive model set."""
    _save_model(config, provider, model)
    console.print(f"[green]✅ Model set:[/] {provider}/{model}")
    console.print("[dim]Restart sgd for changes to take effect.[/]")


def run_list() -> None:
    """List all available providers and their models."""
    table = Table(title="Available AI Providers & Models", show_lines=True)
    table.add_column("Provider", style="bold cyan", width=14)
    table.add_column("Models", style="dim")
    table.add_column("Key Required", justify="center")

    key_required = {
        ProviderName.OPENAI: "OPENAI_API_KEY",
        ProviderName.ANTHROPIC: "ANTHROPIC_API_KEY",
        ProviderName.OPENROUTER: "OPENROUTER_API_KEY",
        ProviderName.OLLAMA: "None (local)",
        ProviderName.DISABLED: "—",
    }

    for pname, models in PROVIDER_MODELS.items():
        table.add_row(
            pname.value,
            "\n".join(models) if models else "—",
            key_required.get(pname, "—"),
        )

    console.print(table)


def _print_provider_table() -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", width=14)
    table.add_column()

    labels = {
        ProviderName.OPENAI: "OpenAI (GPT-4o, GPT-4o-mini)",
        ProviderName.ANTHROPIC: "Anthropic (Claude 3.5 Sonnet)",
        ProviderName.OPENROUTER: "OpenRouter (200+ models, one key)",
        ProviderName.OLLAMA: "Ollama (local, free — no API key)",
        ProviderName.DISABLED: "Disabled — no AI features",
    }
    for pname, label in labels.items():
        table.add_row(pname.value, label)
    console.print(table)


def _save_model(config: str, provider: str, model: str) -> None:
    """Patch [ai] section in the config file using raw TOML string manipulation."""
    import re
    from pathlib import Path

    path = Path(config)
    if not path.exists():
        console.print(f"[red]Config not found: {config}[/]")
        raise typer.Exit(1)

    text = path.read_text()

    # Remove existing [ai] block if present
    text = re.sub(r"\[ai\][^\[]*", "", text, flags=re.DOTALL)
    text = text.rstrip() + "\n"

    # Append new [ai] block
    ai_block = f'\n[ai]\nprovider = "{provider}"\nmodel    = "{model}"\n'
    text += ai_block

    path.write_text(text)
