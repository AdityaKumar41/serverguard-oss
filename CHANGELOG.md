# Changelog

All notable changes to ServerGuard are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] — 2026-06-22

### Added

**Core daemon**
- `sgd` — async Python daemon with full SIGINT/SIGTERM lifecycle management
- TOML configuration loading with strict v1 validation rules
- Polling log file watcher (starts from EOF in production; `--replay` for fixture testing)
- SSH brute-force detector: sliding-window, configurable threshold + window, deduplication
- Normalized event model (id, timestamp, type, severity, source, subject, message, metadata_json)
- SQLite event storage with WAL mode, indexed schema, and atomic writes

**CLI (`sg`)**
- `sg status --config <path>` — Rich-formatted instance status panel with log sources and detectors
- `sg events --config <path>` — Reverse-chronological event table with color-coded severity
- `sg --version` — version flag

**Security hardening**
- Input sanitizer: log line length bounding (4 KiB), null byte / control char stripping, path traversal prevention
- Token-bucket rate limiter: per-source max 10,000 lines/sec, protects against log flooding
- Tamper-evident audit log: SHA-256 hash-chained `audit_chain` SQLite table
- Config file permission check: warns if world-readable
- Data directory permission check: warns if world-writable
- Root user warning at daemon startup

**Audit events**
- `audit.daemon_started` — written on successful daemon startup
- `audit.daemon_stopping` — written on graceful shutdown

**Testing**
- 44 unit + contract tests (pytest + pytest-asyncio)
- Contract tests run against shared fixtures: `tests/fixtures/`

**OSS community**
- MIT License
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`
- GitHub Actions CI (lint + test on every push)
- GitHub issue templates, PR template
- `scripts/install.sh` — one-line installer
- `packaging/serverguard.service` — systemd unit file

### Known Limitations

- Log rotation not yet handled (daemon must be restarted after rotation)
- No notification delivery in v0.0.1 (Slack/Email/Telegram coming in v0.1.0)
- No self-healing actions in v0.0.1 (planned for v0.2.0)
- Port scan detector not yet implemented
- AI anomaly baseline not yet implemented

[0.0.1]: https://github.com/serverguard-oss/serverguard/releases/tag/v0.0.1
