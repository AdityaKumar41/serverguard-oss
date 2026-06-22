"""Unit tests for config loading and validation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from config.loader import load
from config.models import Config, DetectorConfig, LogSource, ServerGuardSection
from config.validator import validate

# ── Fixtures ─────────────────────────────────────────────────────────────────

VALID_TOML = textwrap.dedent("""\
    [serverguard]
    instance_id = "test"
    data_dir = "./data"

    [[log_sources]]
    name = "auth"
    path = "./fixtures/logs/auth.log"
    type = "ssh_auth"

    [[detectors]]
    name = "ssh_bruteforce"
    enabled = true
    source = "auth"
    failed_attempt_threshold = 5
    window_seconds = 60
""")


@pytest.fixture()
def valid_config_file(tmp_path: Path) -> Path:
    p = tmp_path / "config.toml"
    p.write_text(VALID_TOML)
    return p


# ── Tests: happy path ─────────────────────────────────────────────────────────


def test_load_valid_config(valid_config_file: Path) -> None:
    cfg = load(str(valid_config_file))
    assert cfg.serverguard.instance_id == "test"
    assert cfg.serverguard.data_dir == "./data"
    assert len(cfg.log_sources) == 1
    assert len(cfg.detectors) == 1


def test_log_source_fields(valid_config_file: Path) -> None:
    cfg = load(str(valid_config_file))
    ls = cfg.log_sources[0]
    assert ls.name == "auth"
    assert ls.path == "./fixtures/logs/auth.log"
    assert ls.type == "ssh_auth"


def test_detector_fields(valid_config_file: Path) -> None:
    cfg = load(str(valid_config_file))
    d = cfg.detectors[0]
    assert d.name == "ssh_bruteforce"
    assert d.enabled is True
    assert d.source == "auth"
    assert d.failed_attempt_threshold == 5
    assert d.window_seconds == 60


def test_db_path(valid_config_file: Path) -> None:
    cfg = load(str(valid_config_file))
    assert cfg.db_path.endswith("serverguard.db")


# ── Tests: file errors ────────────────────────────────────────────────────────


def test_missing_config_file_raises() -> None:
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load("/nonexistent/path/config.toml")


def test_invalid_toml_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.toml"
    p.write_text("this is not = [[valid toml")
    with pytest.raises(ValueError, match="Invalid TOML"):
        load(str(p))


# ── Tests: validation rules ───────────────────────────────────────────────────


def _make_cfg(**overrides) -> Config:  # type: ignore[no-untyped-def]
    """Build a minimal valid Config, with overrides for specific fields."""
    sg = ServerGuardSection(
        instance_id=overrides.get("instance_id", "test"),
        data_dir=overrides.get("data_dir", "./data"),
    )
    log_sources = overrides.get(
        "log_sources",
        [LogSource(name="auth", path="./auth.log", type="ssh_auth")],
    )
    detectors = overrides.get(
        "detectors",
        [
            DetectorConfig(
                name="ssh_bruteforce",
                enabled=True,
                source="auth",
                failed_attempt_threshold=5,
                window_seconds=60,
            )
        ],
    )
    return Config(serverguard=sg, log_sources=log_sources, detectors=detectors)


def test_empty_instance_id_fails() -> None:
    cfg = _make_cfg(instance_id="")
    with pytest.raises(ValueError, match="instance_id"):
        validate(cfg)


def test_empty_data_dir_fails() -> None:
    cfg = _make_cfg(data_dir="")
    with pytest.raises(ValueError, match="data_dir"):
        validate(cfg)


def test_duplicate_log_source_name_fails() -> None:
    sources = [
        LogSource(name="auth", path="./a.log", type="ssh_auth"),
        LogSource(name="auth", path="./b.log", type="ssh_auth"),
    ]
    cfg = _make_cfg(log_sources=sources)
    with pytest.raises(ValueError, match="duplicate name"):
        validate(cfg)


def test_unsupported_source_type_fails() -> None:
    sources = [LogSource(name="auth", path="./a.log", type="unknown_type")]
    cfg = _make_cfg(log_sources=sources)
    with pytest.raises(ValueError, match="unsupported type"):
        validate(cfg)


def test_detector_references_missing_source_fails() -> None:
    sources = [LogSource(name="auth", path="./a.log", type="ssh_auth")]
    detectors = [
        DetectorConfig(
            name="ssh_bruteforce",
            enabled=True,
            source="nonexistent",
            failed_attempt_threshold=5,
            window_seconds=60,
        )
    ]
    cfg = _make_cfg(log_sources=sources, detectors=detectors)
    with pytest.raises(ValueError, match="unknown log source"):
        validate(cfg)


def test_zero_threshold_fails() -> None:
    sources = [LogSource(name="auth", path="./a.log", type="ssh_auth")]
    detectors = [
        DetectorConfig(
            name="ssh_bruteforce",
            enabled=True,
            source="auth",
            failed_attempt_threshold=0,
            window_seconds=60,
        )
    ]
    cfg = _make_cfg(log_sources=sources, detectors=detectors)
    with pytest.raises(ValueError, match="failed_attempt_threshold"):
        validate(cfg)


def test_zero_window_fails() -> None:
    sources = [LogSource(name="auth", path="./a.log", type="ssh_auth")]
    detectors = [
        DetectorConfig(
            name="ssh_bruteforce",
            enabled=True,
            source="auth",
            failed_attempt_threshold=5,
            window_seconds=0,
        )
    ]
    cfg = _make_cfg(log_sources=sources, detectors=detectors)
    with pytest.raises(ValueError, match="window_seconds"):
        validate(cfg)


def test_duplicate_detector_name_fails() -> None:
    sources = [LogSource(name="auth", path="./a.log", type="ssh_auth")]
    detectors = [
        DetectorConfig(
            name="ssh_bruteforce",
            enabled=True,
            source="auth",
            failed_attempt_threshold=5,
            window_seconds=60,
        ),
        DetectorConfig(
            name="ssh_bruteforce",
            enabled=True,
            source="auth",
            failed_attempt_threshold=3,
            window_seconds=30,
        ),
    ]
    cfg = _make_cfg(log_sources=sources, detectors=detectors)
    with pytest.raises(ValueError, match="duplicate name"):
        validate(cfg)
