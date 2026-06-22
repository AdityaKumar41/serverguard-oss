"""ServerGuard CLI — sg entrypoint.

Commands:
  sg status  --config <path>   Show daemon status and config summary
  sg events  --config <path>   List stored events in reverse chronological order
  sg audit verify --config <path>  Verify tamper-evident audit chain integrity
"""

from __future__ import annotations

import typer
from rich.console import Console

from cli import cmd_status, cmd_events, cmd_audit
from version import __version__

app = typer.Typer(
    name="sg",
    help="[bold green]ServerGuard[/] — autonomous server guardian CLI",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Nested sub-app for `sg audit`
audit_app = typer.Typer(help="Audit log management and verification.", no_args_is_help=True)
app.add_typer(audit_app, name="audit")

console = Console()


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", is_eager=True, help="Show version"),
) -> None:
    if version:
        console.print(f"[bold green]ServerGuard[/] v{__version__}")
        raise typer.Exit()


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


@audit_app.command("verify")
def audit_verify_cmd(
    config: str = typer.Option(..., "--config", "-c", help="Path to config file"),
) -> None:
    """Verify the tamper-evident audit chain for signs of tampering."""
    cmd_audit.run(config)


if __name__ == "__main__":
    app()
