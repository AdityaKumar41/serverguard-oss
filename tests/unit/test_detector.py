"""Unit tests for SSH brute-force detector."""

from __future__ import annotations

from detectors.ssh_bruteforce import SSHBruteforceDetector
from events.model import EVENT_TYPE_SSH_BRUTEFORCE, SEVERITY_WARNING
from parsers.ssh_auth import FailedSSHAttempt


def _attempt(ip: str, username: str = "root", port: int = 22) -> FailedSSHAttempt:
    """Build a minimal FailedSSHAttempt for testing."""
    return FailedSSHAttempt(
        timestamp_text="Apr 25 10:00:00",
        username=username,
        ip=ip,
        port=port,
        raw_line=f"Apr 25 10:00:00 host sshd[1]: Failed password for {username} from {ip} port {port} ssh2",
    )


def _make_detector(threshold: int = 5, window: int = 60) -> SSHBruteforceDetector:
    return SSHBruteforceDetector(source_name="auth", threshold=threshold, window_seconds=window)


# ── Threshold detection ───────────────────────────────────────────────────────

def test_no_event_below_threshold() -> None:
    det = _make_detector(threshold=5)
    events = []
    for _ in range(4):
        events.extend(det.feed(_attempt("1.1.1.1")))
    assert events == [], "Should not emit before threshold is reached"


def test_event_emitted_at_threshold() -> None:
    det = _make_detector(threshold=5)
    events = []
    for _ in range(5):
        events.extend(det.feed(_attempt("1.1.1.1")))
    assert len(events) == 1
    assert events[0].type == EVENT_TYPE_SSH_BRUTEFORCE
    assert events[0].severity == SEVERITY_WARNING
    assert events[0].subject == "1.1.1.1"
    assert events[0].source == "auth"


def test_event_contains_required_metadata() -> None:
    det = _make_detector(threshold=3)
    events = []
    for _ in range(3):
        events.extend(det.feed(_attempt("2.2.2.2")))
    assert len(events) == 1
    meta = events[0].metadata
    assert "attempt_count" in meta
    assert "window_seconds" in meta
    assert "matched_lines" in meta
    assert meta["attempt_count"] == 3
    assert meta["window_seconds"] == 60
    assert len(meta["matched_lines"]) == 3


def test_different_ips_are_tracked_independently() -> None:
    det = _make_detector(threshold=3)
    events = []
    for _ in range(2):
        events.extend(det.feed(_attempt("10.0.0.1")))
    for _ in range(3):
        events.extend(det.feed(_attempt("10.0.0.2")))
    # Only 10.0.0.2 should have triggered.
    assert len(events) == 1
    assert events[0].subject == "10.0.0.2"


# ── Deduplication ─────────────────────────────────────────────────────────────

def test_no_duplicate_event_within_same_window() -> None:
    """Threshold+1 attempts: only one event (last attempt overlaps previous window).

    With threshold=3 and 4 attempts:
      Window 1 ends at index 2 (attempts 0,1,2).
      Attempt 3 forms window [1,2,3] — but window_start=1 <= last_end=2, so suppressed.
    """
    det = _make_detector(threshold=3)
    events = []
    for _ in range(4):  # threshold + 1
        events.extend(det.feed(_attempt("3.3.3.3")))
    assert len(events) == 1, "threshold+1 attempts must emit exactly once"


def test_two_non_overlapping_windows_emit_twice() -> None:
    """2x threshold attempts: two separate windows, two events.

    The spec allows re-emission once new attempts arrive *outside* the
    previous detection window.
    """
    det = _make_detector(threshold=3)
    events = []
    for _ in range(6):  # 2x threshold — two non-overlapping windows
        events.extend(det.feed(_attempt("4.4.4.4")))
    assert len(events) == 2, "Two separate non-overlapping windows should emit twice"


# ── Malformed input ───────────────────────────────────────────────────────────

def test_empty_attempt_list_produces_no_event() -> None:
    det = _make_detector(threshold=5)
    assert list(det.feed(_attempt("9.9.9.9"))) == []


def test_reset_clears_state() -> None:
    det = _make_detector(threshold=3)
    for _ in range(3):
        list(det.feed(_attempt("5.5.5.5")))
    det.reset()
    events = []
    for _ in range(2):
        events.extend(det.feed(_attempt("5.5.5.5")))
    assert events == [], "After reset, threshold should start over"
