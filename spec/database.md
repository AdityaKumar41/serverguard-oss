# ServerGuard Database Specification

## Purpose

This document defines the shared SQLite storage contract for ServerGuard v1.

All implementations must create and use the same logical schema so event storage and CLI inspection remain comparable.

## Database Location

The database file must live at:

```text
<data_dir>/serverguard.db
```

## Engine

The v1 storage engine is SQLite.

No alternative embedded databases are allowed for v1 comparisons.

## Events Table

Required schema:

```sql
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

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject);
```

## ID Rules

Each implementation may choose its own ID generation strategy as long as:

- IDs are unique strings
- IDs are stable after insertion
- IDs are safe to print in CLI output

## Write Rules

The daemon must persist:

- one startup audit event after successful initialization
- one shutdown audit event when graceful shutdown occurs
- one normalized security event for each detector output that passes deduplication rules

## Read Rules

`sg events` must read from the same `events` table and return rows in reverse chronological order.

When two rows have the same timestamp, implementations may choose a deterministic secondary ordering rule.

## Failure Rules

Implementations must return clear errors for:

- database open failure
- schema migration failure
- event insertion failure

Database failures must not silently drop events.
