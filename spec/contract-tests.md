# ServerGuard Contract Tests

## Purpose

Contract tests prove every language implementation follows the same visible behavior.

## Required Fixture Test

Each implementation must support a test named equivalent to `ssh_bruteforce_fixture`.

Input files:

- Config: `fixtures/configs/basic.toml`
- Log: `fixtures/logs/auth.log`
- Expected event: `fixtures/expected-events/ssh-bruteforce.json`

Required behavior:

- load the TOML config successfully
- read the configured auth log
- ignore unrelated and malformed-safe lines
- emit exactly one `security.ssh_bruteforce` event
- persist the event to SQLite when storage is included
- list the event through `sg events` when CLI is included

## Comparison Rules

- Compare event `type`, `severity`, `source`, `subject`, and metadata content.
- Do not compare generated `id` values.
- Do not compare generated audit timestamps exactly.
- `matched_lines` must preserve the original raw log lines.
- Event rows must appear in reverse chronological order for CLI output.

## Failure Rules

The test must fail if:

- no brute-force event is emitted
- more than one brute-force event is emitted for the fixture
- unrelated log lines create security events
- `metadata_json` is invalid JSON
- database errors are ignored
