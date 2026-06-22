"""SSH brute-force detector.

Rule: emit one security.ssh_bruteforce event when the same source IP reaches
at least `failed_attempt_threshold` failed SSH password attempts within
`window_seconds`.

Deduplication rule: after emitting an event for an IP, do not emit another
for that same IP until a new failed attempt arrives outside the previous
detection window.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterator

from detectors.base import Detector
from events.model import (
    EVENT_TYPE_SSH_BRUTEFORCE,
    SEVERITY_WARNING,
    Event,
)
from parsers.ssh_auth import FailedSSHAttempt


class SSHBruteforceDetector(Detector):
    """Sliding-window SSH brute-force detector.

    Tracks failed attempts per source IP. Emits one security.ssh_bruteforce
    event when the threshold is first crossed, then suppresses further events
    until a new attempt arrives outside the last emitted detection window.

    The deduplication invariant:
        After emitting for a window ending at attempt index N,
        the next emission can only happen when a new attempt at index M > N
        causes a new threshold-window [M-threshold+1 .. M] that is
        entirely beyond index N.
    """

    def __init__(self, source_name: str, threshold: int, window_seconds: int) -> None:
        self._source = source_name
        self._threshold = threshold
        self._window = window_seconds

        # Per-IP list of all attempts seen in arrival order.
        self._history: dict[str, list[FailedSSHAttempt]] = defaultdict(list)

        # Per-IP: the 0-based index of the LAST attempt included in the most
        # recently emitted detection window. -1 means "never emitted".
        self._last_emitted_end: dict[str, int] = {}

    def feed(self, attempt: FailedSSHAttempt) -> Iterator[Event]:
        """Feed one parsed attempt. Yields an Event when the rule triggers."""
        ip = attempt.ip
        history = self._history[ip]
        history.append(attempt)

        # We only consider a new window that ENDS at the current (latest) attempt.
        current_end = len(history) - 1  # 0-based index of this attempt

        # Build the candidate window: the last `threshold` attempts.
        if len(history) < self._threshold:
            return  # Not enough attempts yet.

        window_start = len(history) - self._threshold  # inclusive, 0-based
        window_end = current_end  # inclusive, 0-based

        # Deduplication: the window must extend strictly beyond the last
        # emitted window boundary. If the current window end is <= last
        # emitted end, we are still inside the suppression zone.
        last_end = self._last_emitted_end.get(ip, -1)
        if window_end <= last_end:
            return

        # Additionally: the window start must be beyond the last emitted end
        # to ensure we have genuinely new attempts driving this detection.
        # (This prevents re-emitting when only the tail of the old window is
        # re-used with one new attempt.)
        if window_start <= last_end:
            return

        window_attempts = history[window_start : window_end + 1]
        matched_lines = [a.raw_line for a in window_attempts]
        usernames = list({a.username for a in window_attempts})
        ports = [a.port for a in window_attempts if a.port is not None]

        event = Event(
            type=EVENT_TYPE_SSH_BRUTEFORCE,
            severity=SEVERITY_WARNING,
            source=self._source,
            subject=ip,
            message=(
                f"SSH brute-force detected: {len(window_attempts)} failed attempts "
                f"from {ip} within {self._window}s"
            ),
            metadata={
                "attempt_count": len(window_attempts),
                "window_seconds": self._window,
                "matched_lines": matched_lines,
                "usernames": usernames,
                "source_ports": ports,
            },
        )

        # Record this window's end index as the deduplication boundary.
        self._last_emitted_end[ip] = window_end
        yield event

    def reset(self) -> None:
        """Clear all internal state."""
        self._history.clear()
        self._last_emitted_end.clear()
