"""ServerGuard daemon — sgd entrypoint.

Lifecycle:
  1. Parse --config argument
  2. Load and validate config (fail fast on errors)
  3. Open or create SQLite database
  4. Write audit.daemon_started event
  5. Start log watchers + detectors
  6. Run until SIGINT or SIGTERM
  7. Write audit.daemon_stopping event
  8. Shut down cleanly

Usage:
  sgd --config /etc/serverguard/config.toml
  sgd-python --config ./fixtures/configs/basic.toml
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import typer

from config import loader as config_loader
from config.models import Config, DetectorConfig, LogSource
from daemon.watcher import LogWatcher
from detectors.ssh_bruteforce import SSHBruteforceDetector
from events.model import Event, make_daemon_started, make_daemon_stopping
from parsers import ssh_auth
from storage.sqlite import Store
from security.input_sanitizer import (
    check_config_file_permissions,
    check_data_dir_permissions,
)
from security.rate_limiter import RateLimiter

logger = logging.getLogger("serverguard.daemon")


# ── CLI entrypoint ────────────────────────────────────────────────────────────

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def start(
    config: str = typer.Option(..., "--config", "-c", help="Path to TOML config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
    replay: bool = typer.Option(
        False, "--replay", help="Replay existing log content from start (for demos/fixtures)"
    ),
) -> None:
    """ServerGuard daemon — autonomous server guardian."""
    _setup_logging(verbose)
    try:
        cfg = config_loader.load(config)
    except FileNotFoundError as exc:
        typer.echo(f"[ERROR] {exc}", err=True)
        raise typer.Exit(1)
    except ValueError as exc:
        typer.echo(f"[ERROR] Config validation failed: {exc}", err=True)
        raise typer.Exit(1)

    logger.info("Config loaded — instance: %s", cfg.serverguard.instance_id)
    asyncio.run(_run_daemon(cfg, replay=replay))


def main() -> None:
    """Entrypoint for the sgd / sgd-python CLI script."""
    app()


# ── Async daemon core ─────────────────────────────────────────────────────────

async def _run_daemon(cfg: Config, replay: bool = False) -> None:
    """Async daemon loop."""
    # ── Security checks at startup ─────────────────────────────────────────
    if os.geteuid() == 0:
        logger.warning(
            "Running as root is not recommended. "
            "Create a dedicated 'serverguard' user and run as that user."
        )

    check_config_file_permissions(str(cfg.config_path))
    check_data_dir_permissions(str(cfg.serverguard.data_dir))

    # ── Open database ──────────────────────────────────────────────────────
    try:
        store = await Store.open(cfg.db_path)
    except RuntimeError as exc:
        logger.error("Failed to open database: %s", exc)
        sys.exit(1)

    # Audit: daemon started.
    await store.insert(make_daemon_started(cfg.serverguard.instance_id))
    logger.info("Daemon started — watching %d log source(s)", len(cfg.log_sources))
    if replay:
        logger.info("Replay mode: processing existing log content from start")


    # Install signal handlers for clean shutdown.
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    # Build per-source watcher tasks.
    tasks = []
    for ls in cfg.log_sources:
        for det_cfg in cfg.detectors:
            if det_cfg.enabled and det_cfg.source == ls.name:
                task = asyncio.create_task(
                    _watch_source(ls, det_cfg, store, replay=replay),
                    name=f"watcher-{ls.name}",
                )
                tasks.append(task)

    # Wait until a stop signal arrives.
    await stop_event.wait()
    logger.info("Shutdown signal received")

    # Cancel watcher tasks.
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    # Audit: daemon stopping.
    await store.insert(make_daemon_stopping(cfg.serverguard.instance_id))
    await store.close()
    logger.info("Daemon stopped cleanly")


async def _watch_source(
    ls: LogSource, det_cfg: DetectorConfig, store: Store, replay: bool = False
) -> None:
    """Watch one log source and run its configured detector."""
    from security.input_sanitizer import sanitize_log_line

    detector = _build_detector(ls, det_cfg)
    watcher = LogWatcher(ls.path, replay=replay)
    rate_limiter = RateLimiter(source_name=ls.name)
    logger.info("Watching %s → detector: %s", ls.path, det_cfg.name)

    try:
        async for raw_line in watcher.watch():
            # Security: rate limiting (protect against log flooding).
            if not rate_limiter.allow():
                continue

            # Security: sanitize input before any processing.
            line = sanitize_log_line(raw_line)

            attempt = ssh_auth.parse_line(line)
            if attempt is None:
                continue
            for event in detector.feed(attempt):

                logger.warning(
                    "DETECTED [%s] %s — %s",
                    event.type,
                    event.subject,
                    event.message,
                )
                await store.insert(event)
    except FileNotFoundError as exc:
        logger.error("Log source error: %s", exc)
    except asyncio.CancelledError:
        pass


def _build_detector(ls: LogSource, det_cfg: DetectorConfig):  # type: ignore[no-untyped-def]
    """Instantiate the appropriate detector for a config entry."""
    if det_cfg.name == "ssh_bruteforce":
        return SSHBruteforceDetector(
            source_name=ls.name,
            threshold=det_cfg.failed_attempt_threshold,
            window_seconds=det_cfg.window_seconds,
        )
    raise ValueError(f"Unknown detector: {det_cfg.name}")


# ── Logging setup ─────────────────────────────────────────────────────────────

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


if __name__ == "__main__":
    app()
