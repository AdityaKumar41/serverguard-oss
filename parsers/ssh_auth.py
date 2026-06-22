"""SSH auth log parser — extracts structured fields from auth log lines.

Handles lines like:
    Apr 25 10:15:01 host sshd[1234]: Failed password for invalid user admin from 1.2.3.4 port 54321
    Apr 25 10:15:03 host sshd[1235]: Failed password for root from 1.2.3.4 port 54322

Only Failed password lines are matched; all other lines are silently ignored.
Malformed lines that partially match are also ignored — the daemon must not crash.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Matches both "invalid user <name>" and plain username forms.
# Named groups: timestamp, username, ip, port (optional)
_FAILED_RE = re.compile(
    r"^(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)"
    r"\s+\S+"  # hostname
    r"\s+sshd\[\d+\]:"
    r"\s+Failed password for"
    r"(?:\s+invalid user)?"
    r"\s+(?P<username>\S+)"
    r"\s+from\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
    r"(?:\s+port\s+(?P<port>\d+))?",
    re.ASCII,
)


@dataclass
class FailedSSHAttempt:
    """Parsed result from a failed SSH password log line."""

    timestamp_text: str
    username: str
    ip: str
    port: int | None
    raw_line: str


def parse_line(line: str) -> FailedSSHAttempt | None:
    """Parse one auth log line.

    Returns a FailedSSHAttempt if the line represents a failed SSH password
    attempt, or None if it does not match or is malformed.

    This function never raises — all parse errors are suppressed so the
    daemon remains stable on unexpected input.
    """
    try:
        m = _FAILED_RE.match(line.strip())
        if m is None:
            return None
        port_str = m.group("port")
        return FailedSSHAttempt(
            timestamp_text=m.group("timestamp"),
            username=m.group("username"),
            ip=m.group("ip"),
            port=int(port_str) if port_str else None,
            raw_line=line.rstrip("\n"),
        )
    except Exception:  # noqa: BLE001
        return None
