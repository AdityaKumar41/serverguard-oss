"""sg audit verify — verify the tamper-evident audit chain."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from config import loader as config_loader
from security.audit import AuditLog

console = Console()


def run(config: str) -> None:
    """Verify the hash-chained audit log for tampering."""
    try:
        cfg = config_loader.load(config)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise SystemExit(1)

    audit = AuditLog(cfg.audit_db_path)
    ok, errors = audit.verify()
    audit.close()

    if ok:
        console.print(
            Panel(
                "[bold green]✅ Audit chain verified[/]\n"
                "No tampering detected. All hash links are intact.",
                title="[bold]ServerGuard Audit[/]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]⚠️ Audit chain BROKEN[/]\n"
                + "\n".join(f"  • {e}" for e in errors),
                title="[bold red]ServerGuard Audit — TAMPERING DETECTED[/]",
                border_style="red",
            )
        )
        raise SystemExit(2)
