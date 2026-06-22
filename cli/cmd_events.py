"""sg events — list stored security and audit events."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from config import loader as config_loader
from storage.sqlite import SyncStore

console = Console()

# Severity → Rich color mapping.
_SEVERITY_STYLE = {
    "info": "cyan",
    "warning": "yellow",
    "critical": "bold red",
}


def run(config_path: str, limit: int = 50) -> None:
    """Display stored events in reverse chronological order."""
    try:
        cfg = config_loader.load(config_path)
    except FileNotFoundError as exc:
        console.print(f"[bold red]ERROR[/] {exc}")
        raise typer.Exit(1)
    except ValueError as exc:
        console.print(f"[bold red]ERROR[/] Config validation failed: {exc}")
        raise typer.Exit(1)

    try:
        store = SyncStore(cfg.db_path)
    except FileNotFoundError:
        console.print(
            f"[bold yellow]No database found at {cfg.db_path}[/]\n"
            "Run [bold]sgd --config[/] to start the daemon first."
        )
        raise typer.Exit(1)

    events = store.list_events()
    store.close()

    if not events:
        console.print("[dim]No events recorded yet.[/]")
        return

    table = Table(
        "Timestamp",
        "Type",
        "Severity",
        "Source",
        "Subject",
        "Message",
        box=box.ROUNDED,
        title=f"[bold green]ServerGuard Events[/] [dim]({len(events)} total)[/]",
        title_justify="left",
        header_style="bold cyan",
        show_lines=False,
        expand=True,
    )

    for event in events[:limit]:
        sev_style = _SEVERITY_STYLE.get(event.severity, "white")
        # Truncate timestamp to readable form.
        ts = event.timestamp[:19].replace("T", " ")
        table.add_row(
            f"[dim]{ts}[/]",
            _type_label(event.type),
            f"[{sev_style}]{event.severity.upper()}[/]",
            event.source,
            f"[bold]{event.subject}[/]",
            event.message,
        )

    console.print()
    console.print(table)
    console.print()


def _type_label(event_type: str) -> str:
    """Format event type with color coding."""
    if event_type.startswith("audit."):
        return f"[blue]{event_type}[/]"
    if event_type.startswith("security."):
        return f"[red]{event_type}[/]"
    return event_type
