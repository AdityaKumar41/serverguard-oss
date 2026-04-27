# C++ v1 Vertical Slice Design

## Goal

Build the first runnable ServerGuard v1 implementation in C++ so the shared fixture can flow from TOML config to SSH brute-force detection, SQLite event storage, and CLI inspection.

## Approach

The C++ implementation remains small and spec-driven. It will produce research-phase binaries named `sgd-cpp` and `sg-cpp`, while keeping user-visible behavior aligned with the shared `sgd` and `sg` specification.

The first daemon is intentionally minimal: it loads and validates config, scans the configured auth log once, writes startup and shutdown audit events, detects SSH brute force from the fixture, and persists events. Continuous polling and signal handling can follow after the contract path is stable.

## Components

- `config.hpp`: load the simple v1 TOML shape already used by fixtures.
- `config_validate.hpp`: enforce required fields, uniqueness, supported source types, and detector references.
- `ssh_auth.hpp`: parse SSH failed-password auth lines.
- `detector.hpp`: group parsed attempts by IP, apply threshold/window logic, and emit normalized security events.
- `event.hpp`: shared event data structure and JSON escaping helpers.
- `storage.hpp/.cpp`: create/read/write the shared SQLite `events` table.
- `daemon.cpp`: implement `sgd-cpp --config <path>` as the first fixture-processing daemon.
- `cli.cpp`: implement `sg-cpp status --config <path>` and `sg-cpp events --config <path>`.

## SQLite Constraint

This environment has the SQLite shared library but not the development header. Storage will call SQLite through a tiny dynamic loader instead of including `sqlite3.h`. The database remains a real SQLite database at `<data_dir>/serverguard.db`.

## Testing

Development follows TDD for new behavior:

- Add failing tests for config validation, detector event output, and storage.
- Implement the minimum code needed to pass.
- Keep every source file under 100 physical lines.
- Use the existing shared fixtures as the contract source of truth.

