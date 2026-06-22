"""Tamper-evident audit log — hash-chained append-only event records.

Every security event and daemon action is written to a hash-chained
audit table. Each row includes a SHA-256 hash of the previous row's
hash concatenated with the current event's ID and timestamp.

This makes it detectable if audit records are retroactively modified,
deleted, or inserted — the chain will break at the tampered position.

The `sg audit verify` command walks the chain and reports any breaks.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_chain (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id   TEXT NOT NULL,
  timestamp  TEXT NOT NULL,
  action     TEXT NOT NULL,
  actor      TEXT NOT NULL DEFAULT 'daemon',
  detail     TEXT NOT NULL DEFAULT '',
  prev_hash  TEXT NOT NULL,
  chain_hash TEXT NOT NULL
);
"""

_INSERT_AUDIT = """
INSERT INTO audit_chain (event_id, timestamp, action, actor, detail, prev_hash, chain_hash)
VALUES (?, ?, ?, ?, ?, ?, ?);
"""

_GET_LAST_HASH = """
SELECT chain_hash FROM audit_chain ORDER BY seq DESC LIMIT 1;
"""

_GENESIS_HASH = "0" * 64  # Sentinel for the first record.


def _compute_hash(prev_hash: str, event_id: str, timestamp: str, action: str) -> str:
    """Compute SHA-256 chain hash for one audit entry."""
    payload = f"{prev_hash}:{event_id}:{timestamp}:{action}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditLog:
    """Synchronous hash-chained audit log.

    Used inside the daemon (called from async context via run_in_executor
    or directly from sync CLI commands).
    """

    def __init__(self, db_path: str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute(_CREATE_AUDIT_TABLE)
        self._conn.commit()

    def record(
        self,
        event_id: str,
        timestamp: str,
        action: str,
        actor: str = "daemon",
        detail: str = "",
    ) -> None:
        """Append one audit entry to the chain."""
        prev_hash = self._get_last_hash()
        chain_hash = _compute_hash(prev_hash, event_id, timestamp, action)
        self._conn.execute(
            _INSERT_AUDIT,
            (event_id, timestamp, action, actor, detail, prev_hash, chain_hash),
        )
        self._conn.commit()

    def verify(self) -> tuple[bool, list[str]]:
        """Walk the audit chain and return (is_valid, list_of_errors).

        An error is reported for each row where the stored chain_hash
        does not match the recomputed value.
        """
        cursor = self._conn.execute(
            "SELECT seq, event_id, timestamp, action, prev_hash, chain_hash "
            "FROM audit_chain ORDER BY seq ASC;"
        )
        rows = cursor.fetchall()

        errors: list[str] = []
        expected_prev = _GENESIS_HASH

        for seq, event_id, timestamp, action, prev_hash, chain_hash in rows:
            if prev_hash != expected_prev:
                errors.append(
                    f"Chain broken at seq={seq}: "
                    f"expected prev_hash={expected_prev[:12]}… "
                    f"got {prev_hash[:12]}…"
                )
            recomputed = _compute_hash(prev_hash, event_id, timestamp, action)
            if recomputed != chain_hash:
                errors.append(
                    f"Hash mismatch at seq={seq} (event {event_id}): "
                    "audit record may have been tampered with."
                )
            expected_prev = chain_hash

        return (len(errors) == 0, errors)

    def _get_last_hash(self) -> str:
        row = self._conn.execute(_GET_LAST_HASH).fetchone()
        return row[0] if row else _GENESIS_HASH

    def close(self) -> None:
        self._conn.close()
