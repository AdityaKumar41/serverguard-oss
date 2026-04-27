# ServerGuard Event Specification

## Purpose

This document defines the shared event model for ServerGuard v1.

All implementations must store and expose equivalent logical event data even if their internal event structs or classes differ.

## Required Fields

Each event must include:

- `id`
- `timestamp`
- `type`
- `severity`
- `source`
- `subject`
- `message`
- `metadata_json`

## Event Types

Allowed v1 event types:

- `audit.daemon_started`
- `audit.daemon_stopping`
- `security.ssh_bruteforce`

Implementations must not invent additional persisted event types in v1 without updating the shared spec.

## Severities

Allowed v1 severities:

- `info`
- `warning`
- `critical`

## Event Rules

### `audit.daemon_started`

- `severity` must be `info`
- `source` should be `daemon`
- `subject` should be the configured instance ID
- `message` should state that the daemon started

### `audit.daemon_stopping`

- `severity` must be `info`
- `source` should be `daemon`
- `subject` should be the configured instance ID
- `message` should state that the daemon is stopping

### `security.ssh_bruteforce`

- `severity` must be `warning`
- `source` must be the configured log source name
- `subject` must be the source IP address
- `message` should state that repeated failed SSH login attempts were detected

Required metadata fields for `security.ssh_bruteforce`:

- `attempt_count`
- `window_seconds`
- `matched_lines`

Optional metadata fields:

- `usernames`
- `source_ports`

## Timestamp Format

Persisted event timestamps should use an unambiguous machine-readable format.

For v1, implementations should store timestamps in ISO 8601 / RFC 3339 compatible UTC text format when generating new event timestamps themselves.

## Metadata Rules

`metadata_json` must contain valid JSON text.

Implementations may differ in field ordering, but the logical contents must be equivalent.

## Display Rules

The CLI may render a simplified view of event data, but persisted storage must preserve the full required fields.
