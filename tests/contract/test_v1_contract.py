"""Contract tests — run the ServerGuard implementation against shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.loader import load
from events.model import EVENT_TYPE_SSH_BRUTEFORCE
from detectors.ssh_bruteforce import SSHBruteforceDetector
from parsers.ssh_auth import parse_line
from storage.sqlite import Store

# Fixtures live at tests/fixtures/ relative to the repo root.
REPO_ROOT = Path(__file__).parents[2]
FIXTURE_CONFIG = REPO_ROOT / "tests" / "fixtures" / "configs" / "basic.toml"
FIXTURE_LOG = REPO_ROOT / "tests" / "fixtures" / "logs" / "auth.log"


# ── Fixture availability check ────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def require_fixtures() -> None:
    if not FIXTURE_CONFIG.exists():
        pytest.skip(f"Shared fixture not found: {FIXTURE_CONFIG}")
    if not FIXTURE_LOG.exists():
        pytest.skip(f"Shared fixture not found: {FIXTURE_LOG}")


# ── Config contract ───────────────────────────────────────────────────────────

def test_load_shared_fixture_config() -> None:
    """The shared basic.toml must load and validate without error."""
    cfg = load(str(FIXTURE_CONFIG))
    assert cfg.serverguard.instance_id == "local-dev"
    assert len(cfg.log_sources) == 1
    assert len(cfg.detectors) == 1


def test_fixture_config_log_source() -> None:
    cfg = load(str(FIXTURE_CONFIG))
    ls = cfg.log_sources[0]
    assert ls.name == "auth"
    assert ls.type == "ssh_auth"


def test_fixture_config_detector() -> None:
    cfg = load(str(FIXTURE_CONFIG))
    d = cfg.detectors[0]
    assert d.name == "ssh_bruteforce"
    assert d.enabled is True
    assert d.failed_attempt_threshold == 5
    assert d.window_seconds == 60


# ── Detection contract ────────────────────────────────────────────────────────

def test_fixture_log_produces_one_bruteforce_event() -> None:
    """Running the detector against auth.log must yield exactly one SSH brute-force event.

    The fixture contains 5 failed attempts from 203.0.113.10 within 60 seconds,
    plus noise lines that must not trigger detection.
    """
    cfg = load(str(FIXTURE_CONFIG))
    det_cfg = cfg.detectors[0]

    detector = SSHBruteforceDetector(
        source_name="auth",
        threshold=det_cfg.failed_attempt_threshold,
        window_seconds=det_cfg.window_seconds,
    )

    events = []
    for line in FIXTURE_LOG.read_text().splitlines():
        attempt = parse_line(line)
        if attempt is not None:
            events.extend(detector.feed(attempt))

    assert len(events) == 1, f"Expected 1 event, got {len(events)}: {events}"


def test_fixture_bruteforce_event_subject() -> None:
    """The brute-force event subject must be the attacker IP."""
    cfg = load(str(FIXTURE_CONFIG))
    det_cfg = cfg.detectors[0]
    detector = SSHBruteforceDetector(
        source_name="auth",
        threshold=det_cfg.failed_attempt_threshold,
        window_seconds=det_cfg.window_seconds,
    )

    events = []
    for line in FIXTURE_LOG.read_text().splitlines():
        attempt = parse_line(line)
        if attempt is not None:
            events.extend(detector.feed(attempt))

    assert events[0].subject == "203.0.113.10"


def test_fixture_bruteforce_event_type() -> None:
    """The detection event must use the shared event type string."""
    cfg = load(str(FIXTURE_CONFIG))
    det_cfg = cfg.detectors[0]
    detector = SSHBruteforceDetector(
        source_name="auth",
        threshold=det_cfg.failed_attempt_threshold,
        window_seconds=det_cfg.window_seconds,
    )

    events = []
    for line in FIXTURE_LOG.read_text().splitlines():
        attempt = parse_line(line)
        if attempt is not None:
            events.extend(detector.feed(attempt))

    assert events[0].type == EVENT_TYPE_SSH_BRUTEFORCE


def test_fixture_bruteforce_event_metadata() -> None:
    """The detection event must include required metadata fields."""
    cfg = load(str(FIXTURE_CONFIG))
    det_cfg = cfg.detectors[0]
    detector = SSHBruteforceDetector(
        source_name="auth",
        threshold=det_cfg.failed_attempt_threshold,
        window_seconds=det_cfg.window_seconds,
    )

    events = []
    for line in FIXTURE_LOG.read_text().splitlines():
        attempt = parse_line(line)
        if attempt is not None:
            events.extend(detector.feed(attempt))

    meta = events[0].metadata
    assert "attempt_count" in meta
    assert "window_seconds" in meta
    assert "matched_lines" in meta
    assert meta["attempt_count"] >= 5


def test_fixture_non_attacker_ip_does_not_trigger() -> None:
    """198.51.100.30 has only 1 failed attempt in the fixture — must not trigger."""
    cfg = load(str(FIXTURE_CONFIG))
    det_cfg = cfg.detectors[0]
    detector = SSHBruteforceDetector(
        source_name="auth",
        threshold=det_cfg.failed_attempt_threshold,
        window_seconds=det_cfg.window_seconds,
    )

    events = []
    for line in FIXTURE_LOG.read_text().splitlines():
        attempt = parse_line(line)
        if attempt is not None:
            events.extend(detector.feed(attempt))

    triggered_ips = {e.subject for e in events}
    assert "198.51.100.30" not in triggered_ips


# ── Storage contract ──────────────────────────────────────────────────────────

async def test_sqlite_event_roundtrip(tmp_path: Path) -> None:
    """Events written to SQLite must be readable with equivalent logical fields."""
    from events.model import Event, SEVERITY_WARNING

    db_path = str(tmp_path / "serverguard.db")
    store = await Store.open(db_path)

    event = Event(
        type=EVENT_TYPE_SSH_BRUTEFORCE,
        severity=SEVERITY_WARNING,
        source="auth",
        subject="203.0.113.10",
        message="SSH brute-force detected: 5 attempts in 60s",
        metadata={"attempt_count": 5, "window_seconds": 60, "matched_lines": []},
    )
    await store.insert(event)
    events = await store.list_events()
    await store.close()

    assert len(events) == 1
    r = events[0]
    assert r.id == event.id
    assert r.type == EVENT_TYPE_SSH_BRUTEFORCE
    assert r.subject == "203.0.113.10"
    assert r.severity == SEVERITY_WARNING
    assert r.metadata["attempt_count"] == 5
