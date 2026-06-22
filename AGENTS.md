# ServerGuard — Development Guide

Instructions for AI coding assistants and developers working on the ServerGuard codebase.

**Never give up on the right solution. Security is not negotiable.**

---

## What ServerGuard Is

ServerGuard is an autonomous server guardian that runs as a lightweight Python daemon on any Linux or macOS server. It monitors system logs in real time, detects threats (SSH brute-force, port scans, anomalies), delivers incident alerts to Telegram/Discord/Slack/Email, runs an AI enrichment loop to explain and contextualize threats, and self-improves its detection thresholds from experience.

It ships as a single CLI (`sg` + `sgd`) installable via pip/pipx. It is extended through **detectors, notifiers, and agent plugins** — not by growing the daemon core.

Two properties shape every design decision:

- **The daemon core is a narrow waist.** The daemon loop is intentionally minimal: read logs → parse → detect → store → notify. Every addition to the core loop is expensive in CPU, memory, and maintenance. New capability must land as a new detector, notifier, or agent module — not inside the daemon loop itself.
- **Security properties must never degrade.** Input sanitization, rate limiting, audit chaining, and privilege checks are non-negotiable. A fix that weakens any of these to solve a different problem is the wrong fix.

---

## Project Structure

```
serverguard/                         ← repo root
├── config/                          ← TOML config loading + validation
│   ├── loader.py                    load() entry point
│   ├── models.py                    Config, LogSource, DetectorConfig dataclasses
│   └── validator.py                 validate() — strict contract checks
├── parsers/
│   └── ssh_auth.py                  Regex parser for auth.log / secure lines
├── events/
│   └── model.py                     Event dataclass + factory functions
├── storage/
│   └── sqlite.py                    Store — aiosqlite WAL-mode event store
├── detectors/
│   ├── base.py                      Detector ABC
│   └── ssh_bruteforce.py            Sliding-window SSH brute-force detector
├── security/
│   ├── input_sanitizer.py           Log line cleaning, path traversal prevention
│   ├── rate_limiter.py              Token-bucket flood protection per source
│   └── audit.py                     SHA-256 hash-chained audit log
├── daemon/
│   ├── daemon.py                    sgd entry point — async lifecycle + signal handling
│   └── watcher.py                   Async log file tail with replay mode
├── cli/
│   ├── main.py                      sg CLI root + sub-app wiring
│   ├── cmd_setup.py                 sg setup wizard (AI + notifications + log sources)
│   ├── cmd_model.py                 sg model provider switcher
│   ├── cmd_status.py                sg status
│   ├── cmd_events.py                sg events
│   ├── cmd_ask.py                   sg ask (AI Q&A over event history)
│   └── cmd_audit.py                 sg audit verify
├── notifiers/
│   ├── base.py                      Notifier ABC + build_notifiers() factory
│   ├── telegram.py                  Telegram Bot API (markdown + AI summary + geo)
│   ├── discord.py                   Discord webhook (rich embeds)
│   ├── slack.py                     Slack incoming webhook (Block Kit)
│   ├── webhook.py                   Generic HMAC-signed HTTP POST
│   └── email.py                     SMTP (async-safe, STARTTLS)
├── agent/
│   ├── providers.py                 ProviderName enum + AIConfig dataclass
│   ├── client.py                    Async OpenAI-compat chat completions client
│   ├── enrichment.py                IP geo + AI summary enrichment per event
│   └── learner.py                   Self-learning loop — AI analyzes patterns
├── gateway/
│   └── telegram_bot.py              Long-polling Telegram bot (/status, /events, /ask)
├── tests/
│   ├── fixtures/                    Shared log + config fixtures
│   ├── unit/                        Unit tests per module
│   └── contract/                    Contract tests run against shared fixtures
├── docs/                            User-facing documentation
├── scripts/
│   └── install.sh                   One-line installer
├── packaging/
│   └── serverguard.service          Hardened systemd unit
├── .github/
│   ├── workflows/ci.yml             Lint + test on Python 3.11/3.12/3.13
│   └── workflows/release.yml        PyPI publish + GitHub Release on tag
├── version.py                       __version__ = "0.0.1"
├── pyproject.toml                   Flat layout, entry points: sg + sgd
└── Makefile                         install-dev / test / lint / run-*
```

---

## Contribution Rubric — What We Want / What We Don't

### What We Want

- **Fix real bugs, well.** Reproduce the bug on current `main`, point to the exact line, fix the whole bug class — not just the one reported site. Sibling call paths included.
- **New detectors in `detectors/`.** A new detector (port scan, log injection, anomaly scoring) is always welcome. It must extend `Detector`, add a fixture file in `tests/fixtures/`, and pass contract tests.
- **New notifiers in `notifiers/`.** A new delivery channel (Matrix, PagerDuty, ntfy.sh, etc.) is always welcome. It must extend `Notifier`, use env vars for secrets, and never raise from `send()`.
- **New AI providers in `agent/providers.py`.** Add the provider to `ProviderName`, `PROVIDER_MODELS`, and `PROVIDER_BASE_URLS`. The `client.py` is provider-agnostic (OpenAI-compat format).
- **Security hardening.** Any PR that improves input validation, tightens permissions, adds audit coverage, or reduces attack surface is a high-priority merge.
- **Self-improvement features.** The `agent/learner.py` pattern (observe → analyze → suggest → persist) is the right model for all AI-driven adaptation. Extend it, don't bypass it.
- **Behavior contracts over snapshots.** Tests assert invariants (event count relation, severity ordering, chain validity) — not frozen values (model lists, config version literals).
- **E2E validation.** For security paths, exercise the real runtime path against `tests/fixtures/` — not just mocked internals.

### What We Don't Want

- **Secrets in config.toml.** API keys, bot tokens, SMTP passwords — all live in environment variables or `.env`. The TOML file must remain safe to commit to a private repo.
- **New daemon-core features when a module would do.** If a new capability can be a detector or notifier, it must be. The daemon loop is frozen at: parse → detect → store → enrich → notify.
- **Blocking operations in async context.** The daemon is fully async. Any blocking call (SMTP, file I/O, subprocess) must use `loop.run_in_executor`. SMPT is the one current exception, already wrapped.
- **Change-detector tests.** Tests that assert exact model lists, exact threshold values, or exact version strings are brittle and unwanted.
- **Silently degrading security.** A notifier that swallows all exceptions is correct behavior. A security module (sanitizer, rate limiter, audit) that swallows exceptions to keep running is not.
- **Outbound telemetry.** ServerGuard never sends usage data, analytics, or attribution tags. Zero. If you add a network call that is not directly serving the user's configured notifier or AI provider, it will be rejected.
- **Root-only assumptions.** The daemon must work when running as a non-root user with read access to log files. Never assume `/var/log/auth.log` is always readable.

---

## Architecture: The Daemon Loop

```
                    ┌──────────┐
log file ──tail──▶ │ Watcher  │
                    └─────┬────┘
                          │ raw line
                          ▼
                    ┌──────────────┐
                    │ Sanitizer    │  (security/input_sanitizer.py)
                    │ Rate Limiter │  (security/rate_limiter.py)
                    └─────┬────────┘
                          │ clean line
                          ▼
                    ┌──────────┐
                    │ Parser   │  (parsers/ssh_auth.py, etc.)
                    └─────┬────┘
                          │ ParsedAttempt
                          ▼
                    ┌──────────┐
                    │ Detector │  (detectors/ssh_bruteforce.py, etc.)
                    └─────┬────┘
                          │ Event (if threshold crossed)
                          ▼
                    ┌──────────┐
                    │ Store    │  (storage/sqlite.py)  → audit_chain
                    └─────┬────┘
                          │ stored Event
                    ┌──────────────────────────────┐
                    │  async (non-blocking)         │
                    │  ├─ Enrichment (agent/)       │  AI summary + geo
                    │  ├─ Learner   (agent/)        │  pattern analysis
                    │  └─ Notifiers (notifiers/)    │  Telegram/Discord/...
                    └──────────────────────────────┘
```

**Key invariant**: enrichment, learning, and notification are always fire-and-forget async tasks. They never block or delay the next log line being read.

---

## The Footprint Ladder (New Capability Decision)

Each rung adds more permanent daemon surface than the one above. Choose the highest rung that correctly solves the problem:

1. **Extend an existing module** — a variation of something already implemented. Zero new surface.
2. **New detector** — new log parsing + threshold logic. Lives in `detectors/`. Zero daemon-core changes.
3. **New notifier** — new delivery channel. Lives in `notifiers/`. Zero daemon-core changes.
4. **New agent module** — new AI-driven analysis or enrichment. Lives in `agent/`. Async only.
5. **New gateway** — new messaging platform bot. Lives in `gateway/`. Runs as separate process.
6. **New daemon-core feature** — only if the capability is fundamental and unreachable by the above rungs.

---

## Security Review Checklist

Every PR touching security-adjacent code must be reviewed against:

- [ ] All external input (log lines, config values, notifier payloads) passes through `security/input_sanitizer.py`
- [ ] Rate limiting is applied before any processing of log lines
- [ ] No secrets appear in config.toml, code, tests, or log output
- [ ] Audit log records the new event type if it represents a daemon state change
- [ ] Config and data directory permissions are checked at startup (not silently assumed)
- [ ] Systemd unit restrictions still hold (no new filesystem writes outside `ReadWritePaths`)
- [ ] The PR does not add outbound network calls not explicitly configured by the user

---

## Running the Full Stack

```bash
# Install dev environment
make install-dev

# Run all tests (44+ unit + contract)
make test

# Lint
make lint

# Start daemon with fixture replay (detects SSH brute-force from test log)
make run-daemon

# CLI commands
make run-status
make run-events

# Verify tamper-evident audit chain
make audit-verify

# Setup wizard
.venv/bin/sg setup
```

---

## Adding a Detector

1. Create `detectors/<name>.py`, extending `Detector` from `detectors/base.py`
2. Implement `feed(attempt) -> list[Event]`
3. Add a fixture log file in `tests/fixtures/logs/<name>.log`
4. Add a contract test in `tests/contract/test_<name>_contract.py`
5. Register in `daemon/daemon.py → _build_detector()` switch
6. Document in `docs/detectors.md`

---

## Adding a Notifier

1. Create `notifiers/<name>.py`, extending `Notifier` from `notifiers/base.py`
2. Implement `send(event)` (must not raise — log + swallow)
3. Implement `from_config(block)` — loads secrets from environment only
4. Register in `notifiers/base.py → build_notifiers() → type_map`
5. Add env var template to `.env.example`
6. Add setup step in `cli/cmd_setup.py → _configure_notifier()`

---

## Adding an AI Provider

1. Add to `ProviderName` enum in `agent/providers.py`
2. Add models list to `PROVIDER_MODELS`
3. Add base URL to `PROVIDER_BASE_URLS`
4. Add API key env var to `api_key()` method's `env_map`
5. Add to `sg setup` provider picker (`cli/cmd_setup.py → _PROVIDER_CHOICES`)
6. Add to `.env.example`

---

## File Dependency Chain

```
version.py  (no deps — imported by cli/main.py)
events/model.py  (no deps — imported by all event-producing modules)
       ↑
parsers/*.py  (pure parsing, no storage deps)
       ↑
detectors/*.py  (imports events.model + parsers)
       ↑
storage/sqlite.py  (imports events.model)
       ↑
security/*.py  (no serverguard deps)
       ↑
agent/*.py  (imports events.model, uses httpx)
notifiers/*.py  (imports events.model, uses httpx)
gateway/*.py  (imports storage, agent)
       ↑
daemon/daemon.py  (imports all of the above — orchestration only)
cli/main.py  (imports cli/* modules)
```

---

## Verification Plan for Every PR

1. `make test` — all tests pass
2. `make lint` — ruff clean
3. `make run-daemon` — detects brute-force from fixture log
4. `sg audit verify` — audit chain intact
5. For notifier PRs: at minimum a manual send test against a real channel
6. For detector PRs: contract test with real fixture log demonstrates detection + non-detection

---

*ServerGuard is open source under MIT. Contributions welcome — see CONTRIBUTING.md.*
