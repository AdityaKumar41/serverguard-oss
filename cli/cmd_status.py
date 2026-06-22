"""sg status — show daemon configuration and database status."""

from __future__ import annotations

import os

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import loader as config_loader

console = Console()


def run(config_path: str) -> None:
    """Display ServerGuard instance status."""
    try:
        cfg = config_loader.load(config_path)
    except FileNotFoundError:
        console.print("[bold red]ERROR[/] Config file not found")
        raise typer.Exit(1) from None
    except ValueError as exc:
        console.print(f"[bold red]ERROR[/] Config validation failed: {exc}")
        raise typer.Exit(1) from None

    db_exists = os.path.exists(cfg.db_path)
    db_status = "[green]exists[/]" if db_exists else "[yellow]not created yet[/]"

    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=26)
    table.add_column("Value", style="white")

    table.add_row("Instance ID", cfg.serverguard.instance_id)
    table.add_row("Data Directory", cfg.serverguard.data_dir)
    table.add_row("Database Path", cfg.db_path)
    table.add_row("Database Status", db_status)
    table.add_row("Log Sources", str(len(cfg.log_sources)))
    table.add_row("Detectors", str(len(cfg.detectors)))

    console.print()
    console.print(
        Panel(
            table,
            title="[bold green]⚡ ServerGuard Status[/]",
            border_style="green",
            expand=False,
        )
    )

    if cfg.log_sources:
        src_table = Table(
            "Name",
            "Type",
            "Path",
            box=box.SIMPLE_HEAD,
            style="dim",
            title="[cyan]Log Sources[/]",
            title_style="bold cyan",
        )
        for ls in cfg.log_sources:
            src_table.add_row(ls.name, ls.type, ls.path)
        console.print(src_table)

    if cfg.detectors:
        det_table = Table(
            "Name",
            "Enabled",
            "Source",
            "Threshold",
            "Window",
            box=box.SIMPLE_HEAD,
            style="dim",
            title="[magenta]Detectors[/]",
            title_style="bold magenta",
        )
        for d in cfg.detectors:
            det_table.add_row(
                d.name,
                "[green]yes[/]" if d.enabled else "[red]no[/]",
                d.source,
                str(d.failed_attempt_threshold),
                f"{d.window_seconds}s",
            )
        console.print(det_table)
    console.print()
