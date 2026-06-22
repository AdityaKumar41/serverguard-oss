"""TOML configuration loader for ServerGuard."""

from __future__ import annotations

import tomllib
from pathlib import Path

from config.models import Config, DetectorConfig, LogSource, ServerGuardSection
from config.validator import validate


def load(config_path: str) -> Config:
    """Load and validate a TOML config file.

    Raises:
        FileNotFoundError: if the config file does not exist.
        ValueError: if the TOML is invalid or fails validation.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid TOML in {config_path}: {exc}") from exc

    config = _parse(raw)
    config.config_path = str(path.resolve())
    validate(config)
    return config


def _parse(raw: dict) -> Config:  # type: ignore[type-arg]
    """Convert raw TOML dict into Config dataclasses."""
    sg_raw = raw.get("serverguard", {})
    serverguard = ServerGuardSection(
        instance_id=sg_raw.get("instance_id", ""),
        data_dir=sg_raw.get("data_dir", ""),
    )

    log_sources = [
        LogSource(
            name=ls.get("name", ""),
            path=ls.get("path", ""),
            type=ls.get("type", ""),
        )
        for ls in raw.get("log_sources", [])
    ]

    detectors = [
        DetectorConfig(
            name=d.get("name", ""),
            enabled=bool(d.get("enabled", False)),
            source=d.get("source", ""),
            failed_attempt_threshold=int(d.get("failed_attempt_threshold", 0)),
            window_seconds=int(d.get("window_seconds", 0)),
        )
        for d in raw.get("detectors", [])
    ]

    return Config(
        serverguard=serverguard,
        log_sources=log_sources,
        detectors=detectors,
    )
