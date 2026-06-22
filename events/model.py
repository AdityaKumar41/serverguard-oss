"""Event model — shared data contract for all ServerGuard events."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# ── Allowed event types (v1) ─────────────────────────────────────────────────
EVENT_TYPE_DAEMON_STARTED = "audit.daemon_started"
EVENT_TYPE_DAEMON_STOPPING = "audit.daemon_stopping"
EVENT_TYPE_SSH_BRUTEFORCE = "security.ssh_bruteforce"

# ── Allowed severities (v1) ──────────────────────────────────────────────────
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"


@dataclass
class Event:
    """A normalized ServerGuard security or audit event.

    All fields map directly to the shared SQLite schema defined in spec/database.md.
    """

    type: str
    severity: str
    source: str
    subject: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def metadata_json(self) -> str:
        """Serialize metadata dict to a JSON string for storage."""
        return json.dumps(self.metadata)

    @classmethod
    def from_row(cls, row: tuple) -> Event:  # type: ignore[type-arg]
        """Reconstruct an Event from a SQLite row tuple.

        Row order: id, timestamp, type, severity, source, subject, message, metadata_json
        """
        id_, ts, type_, severity, source, subject, message, meta_json = row
        return cls(
            id=id_,
            timestamp=ts,
            type=type_,
            severity=severity,
            source=source,
            subject=subject,
            message=message,
            metadata=json.loads(meta_json),
        )


def make_daemon_started(instance_id: str) -> Event:
    """Create an audit.daemon_started event."""
    return Event(
        type=EVENT_TYPE_DAEMON_STARTED,
        severity=SEVERITY_INFO,
        source="daemon",
        subject=instance_id,
        message=f"ServerGuard daemon started (instance: {instance_id})",
    )


def make_daemon_stopping(instance_id: str) -> Event:
    """Create an audit.daemon_stopping event."""
    return Event(
        type=EVENT_TYPE_DAEMON_STOPPING,
        severity=SEVERITY_INFO,
        source="daemon",
        subject=instance_id,
        message=f"ServerGuard daemon stopping (instance: {instance_id})",
    )
