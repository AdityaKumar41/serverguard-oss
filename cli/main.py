"""ServerGuard CLI — sg entrypoint.

Commands:
  sg setup                         Interactive setup wizard
  sg model                         Switch AI model provider
  sg model set <provider> <model>  Set model non-interactively
  sg model list                    List all available providers
  sg status  --config <path>       Show daemon status
  sg events  --config <path>       List stored events
  sg ask     --config <path> <q>   Ask AI about server security
  sg audit verify --config <path>  Verify tamper-evident audit chain
"""

from __future__ import annotations

import typer
from rich.console import Console

from cli import cmd_ask, cmd_audit, cmd_events, cmd_model, cmd_setup, cmd_status

__version__ = "0.0.1"

app = typer.Typer(
    name="sg",
    help=(
        "[bold green]ServerGuard[/] — autonomous server guardian.\n\n"
        "Run [bold cyan]sg setup[/] to get started."
    ),
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ── Sub-apps ──────────────────────────────────────────────────────────────────

audit_app = typer.Typer(help="Audit log management and verification.", no_args_is_help=True)
app.add_typer(audit_app, name="audit")

model_app = typer.Typer(help="AI model provider management.", no_args_is_help=True)
app.add_typer(model_app, name="model")

console = Console()


# ── Root ──────────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", is_eager=True, help="Show version"),
) -> None:
    if version:
        console.print(f"[bold green]ServerGuard[/] v{__version__}")
        raise typer.Exit()


# ── Core commands ─────────────────────────────────────────────────────────────


@app.command("setup")
def setup_cmd() -> None:
    """Interactive setup wizard — configure AI provider, notifications, and log sources."""
    cmd_setup.run()


@app.command("status")
def status_cmd(
    config: str = typer.Option(..., "--config", "-c", help="Path to config file"),
) -> None:
    """Show daemon configuration and database status."""
    cmd_status.run(config)


@app.command("events")
def events_cmd(
    config: str = typer.Option(..., "--config", "-c", help="Path to config file"),
    limit: int = typer.Option(50, "--limit", "-n", help="Max events to display"),
) -> None:
    """List stored events in reverse chronological order."""
    cmd_events.run(config, limit=limit)


@app.command("ask")
def ask_cmd(
    question: str = typer.Argument(..., help="Your security question"),
    config: str = typer.Option(..., "--config", "-c", help="Path to config file"),
) -> None:
    """Ask AI a question about your server's security history."""
    cmd_ask.run(config, question)


# ── Model sub-commands ────────────────────────────────────────────────────────


@model_app.callback(invoke_without_command=True)
def model_root(ctx: typer.Context) -> None:
    """Switch AI model provider interactively."""
    if ctx.invoked_subcommand is None:
        config = typer.prompt("Config path", default=str(cmd_setup.DEFAULT_CONFIG))
        cmd_model.run_interactive(config)


@model_app.command("set")
def model_set_cmd(
    provider: str = typer.Argument(..., help="Provider (openai, anthropic, openrouter, ollama)"),
    model: str = typer.Argument(..., help="Model name"),
    config: str = typer.Option(..., "--config", "-c", help="Path to config file"),
) -> None:
    """Set AI provider and model non-interactively."""
    cmd_model.run_set(config, provider, model)


@model_app.command("list")
def model_list_cmd() -> None:
    """List all available AI providers and models."""
    cmd_model.run_list()


# ── Audit sub-commands ────────────────────────────────────────────────────────


@audit_app.command("verify")
def audit_verify_cmd(
    config: str = typer.Option(..., "--config", "-c", help="Path to config file"),
) -> None:
    """Verify the tamper-evident audit chain for signs of tampering."""
    cmd_audit.run(config)


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
