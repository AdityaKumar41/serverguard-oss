"""SQLite event store — implements the shared v1 database schema.

Schema (from spec/database.md):

    CREATE TABLE IF NOT EXISTS events (
      id TEXT PRIMARY KEY,
      timestamp TEXT NOT NULL,
      type TEXT NOT NULL,
      severity TEXT NOT NULL,
      source TEXT NOT NULL,
      subject TEXT NOT NULL,
      message TEXT NOT NULL,
      metadata_json TEXT NOT NULL
    );
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import aiosqlite

from events.model import Event

_CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  type TEXT NOT NULL,
  severity TEXT NOT NULL,
  source TEXT NOT NULL,
  subject TEXT NOT NULL,
  message TEXT NOT NULL,
  metadata_json TEXT NOT NULL
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);",
    "CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject);",
]

_INSERT_EVENT = """
INSERT INTO events (id, timestamp, type, severity, source, subject, message, metadata_json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

_SELECT_EVENTS_DESC = """
SELECT id, timestamp, type, severity, source, subject, message, metadata_json
FROM events
ORDER BY timestamp DESC;
"""


class Store:
    """Async SQLite event store.

    Usage:
        store = await Store.open("/path/to/serverguard.db")
        await store.insert(event)
        async for event in store.list_events():
            ...
        await store.close()
    """

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    @classmethod
    async def open(cls, db_path: str) -> Store:
        """Open or create the database and apply the v1 schema.

        Raises:
            RuntimeError: if the database cannot be opened or migrated.
        """
        path = Path(db_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            db = await aiosqlite.connect(str(path))
            db.row_factory = aiosqlite.Row
            await db.execute(_CREATE_EVENTS_TABLE)
            for idx_sql in _CREATE_INDEXES:
                await db.execute(idx_sql)
            await db.commit()
            return cls(db)
        except Exception as exc:
            raise RuntimeError(f"Database open/migration failed at {db_path}: {exc}") from exc

    async def insert(self, event: Event) -> None:
        """Persist one event. Never silently drops — raises on failure."""
        try:
            await self._db.execute(
                _INSERT_EVENT,
                (
                    event.id,
                    event.timestamp,
                    event.type,
                    event.severity,
                    event.source,
                    event.subject,
                    event.message,
                    event.metadata_json,
                ),
            )
            await self._db.commit()
        except Exception as exc:
            raise RuntimeError(f"Event insertion failed: {exc}") from exc

    async def list_events(self) -> list[Event]:
        """Return all events in reverse chronological order."""
        try:
            async with self._db.execute(_SELECT_EVENTS_DESC) as cursor:
                rows = await cursor.fetchall()
            return [Event.from_row(tuple(row)) for row in rows]
        except Exception as exc:
            raise RuntimeError(f"Event listing failed: {exc}") from exc

    async def close(self) -> None:
        """Close the database connection."""
        await self._db.close()


def open_store_sync(db_path: str) -> SyncStore:
    """Open a synchronous store for CLI commands that don't use asyncio."""
    return SyncStore(db_path)


class SyncStore:
    """Synchronous wrapper for CLI read-only access."""

    def __init__(self, db_path: str) -> None:
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row

    def list_events(self) -> list[Event]:
        """Return all events in reverse chronological order."""
        cursor = self._conn.execute(_SELECT_EVENTS_DESC)
        return [Event.from_row(tuple(row)) for row in cursor.fetchall()]

    def close(self) -> None:
        self._conn.close()
