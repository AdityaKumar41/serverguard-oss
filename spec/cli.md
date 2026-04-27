# ServerGuard CLI Specification

## Purpose

This document defines the shared v1 CLI behavior.

All implementations must support the same commands and expose the same logical output fields even if formatting differs slightly during early research.

## Commands

Required commands:

```text
sg status --config <path>
sg events --config <path>
```

## `sg status`

This command must show:

- instance ID
- data directory
- database path
- configured log source count
- configured detector count

For v1, the CLI may read configuration and SQLite state directly. Daemon IPC is not required yet.

## `sg events`

This command must:

- open the configured SQLite database
- read from the shared `events` table
- show events in reverse chronological order

Required output fields:

- timestamp
- type
- severity
- source
- subject
- message

Implementations may optionally include the event ID.

## Exit Behavior

Commands must return non-zero exit status on:

- missing config file
- invalid config
- missing database
- database read failure

The exact numeric code may differ in v1, but success and failure behavior must remain consistent.
