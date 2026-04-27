# ServerGuard v1 Specification

## Purpose

ServerGuard v1 defines the first comparable product slice for the Go, Rust, and C++ implementations.

This specification is language-neutral. Each implementation may use idiomatic internal architecture, but all implementations must expose the same behavior, configuration format, event format, storage schema, CLI commands, and test results.

Supporting documents:

- [config.md](config.md)
- [events.md](events.md)
- [database.md](database.md)
- [detection-rules.md](detection-rules.md)
- [cli.md](cli.md)
- [implementation-rules.md](implementation-rules.md)
- [contract-tests.md](contract-tests.md)

## Scope

ServerGuard v1 is a local-first server monitoring and detection daemon with a companion CLI.

The v1 slice includes:

- daemon lifecycle
- configuration loading
- log file watching
- SSH brute-force detection
- normalized security events
- local SQLite event storage
- basic CLI status and event listing
- clean shutdown behavior
- basic audit logging

The v1 slice does not include:

- real firewall blocking
- certificate renewal
- service restart remediation
- plugin system
- remote dashboard
- distributed agents
- machine learning detection
- privileged kernel integrations

Those features are intentionally postponed so the first comparison stays measurable.

## Binaries

Each implementation must provide two executable entry points:

- `sgd`: ServerGuard daemon
- `sg`: ServerGuard CLI

During the research phase, each language implementation may add a language suffix for local development, such as `sgd-go`, `sgd-rust`, or `sgd-cpp`, but the user-facing behavior must match this specification.

## Daemon Behavior

The daemon must:

- start from a config file path
- validate the config before starting watchers
- open or create the local SQLite database
- write an audit event after startup
- watch configured log files
- run configured detectors
- persist normalized events
- expose enough local state for the CLI to report status
- handle `SIGINT` and `SIGTERM`
- stop watchers cleanly during shutdown
- write an audit event before shutdown when possible

The daemon must fail fast if required configuration is invalid.

## Configuration

The v1 config format is TOML.

Required top-level fields:

```toml
[serverguard]
instance_id = "local-dev"
data_dir = "./data"

[[log_sources]]
name = "auth"
path = "./fixtures/logs/auth.log"
type = "ssh_auth"

[[detectors]]
name = "ssh_bruteforce"
enabled = true
source = "auth"
failed_attempt_threshold = 5
window_seconds = 60
```

Required validation rules:

- `serverguard.instance_id` must be non-empty
- `serverguard.data_dir` must be non-empty
- each `log_sources.name` must be unique
- each `log_sources.path` must be non-empty
- each `log_sources.type` must be supported
- each `detectors.name` must be unique
- each enabled detector must reference an existing log source
- `failed_attempt_threshold` must be greater than zero
- `window_seconds` must be greater than zero

## Log Watching

The daemon must support watching a plain text log file.

For v1, the watcher may poll the file instead of using platform-specific file notification APIs. This keeps behavior easier to compare across languages.

The watcher must:

- read new lines from the configured file
- avoid rereading already processed lines during one daemon run
- tolerate empty files
- tolerate lines that do not match any detector
- continue running when a non-matching line is seen
- produce a clear error if the configured file does not exist at startup

Log rotation handling is not required in v1.

## SSH Brute-Force Detection

The v1 detector must detect repeated failed SSH login attempts from the same source IP within a configured time window.

The detector input is a stream of auth log lines.

The detector must identify lines equivalent to:

```text
Apr 25 10:15:01 host sshd[1234]: Failed password for invalid user admin from 203.0.113.10 port 54321 ssh2
Apr 25 10:15:03 host sshd[1235]: Failed password for root from 203.0.113.10 port 54322 ssh2
```

Minimum fields extracted:

- timestamp text from the log line
- username when present
- source IP address
- source port when present
- raw line

Detection rule:

When the same source IP has at least `failed_attempt_threshold` failed SSH password attempts inside `window_seconds`, emit one `security.ssh_bruteforce` event.

Deduplication rule:

After emitting an event for an IP address, the detector must not emit another event for the same IP address until a new failed attempt arrives outside the previous detection window.

Malformed or unsupported lines must not crash the daemon.

## Event Model

All stored events must use the same logical fields.

Required fields:

- `id`
- `timestamp`
- `type`
- `severity`
- `source`
- `subject`
- `message`
- `metadata_json`

Allowed event types for v1:

- `audit.daemon_started`
- `audit.daemon_stopping`
- `security.ssh_bruteforce`

Allowed severities for v1:

- `info`
- `warning`
- `critical`

For SSH brute-force events:

- `type` must be `security.ssh_bruteforce`
- `severity` must be `warning`
- `source` must be the log source name
- `subject` must be the source IP address
- `metadata_json` must include the attempt count and matched log lines

## Storage

ServerGuard v1 uses SQLite for local event storage.

The database file must live under:

```text
<data_dir>/serverguard.db
```

The v1 schema must include an `events` table:

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

Each implementation may choose its own ID generation strategy as long as IDs are unique strings.

## CLI Behavior

The CLI must support these commands:

```text
sg status --config <path>
sg events --config <path>
```

For v1, the CLI may read status and events directly from the configured data directory instead of requiring daemon IPC.

`sg status` must show:

- instance ID
- data directory
- database path
- configured log source count
- configured detector count

`sg events` must show stored events in reverse chronological order.

The exact table formatting may differ during early research, but the same fields must be present.

## Error Handling

Implementations must return clear errors for:

- missing config file
- invalid TOML
- invalid required config field
- missing configured log file
- database open failure
- database schema migration failure

Malformed log lines must be ignored or recorded as debug information, but they must not crash the daemon.

## Test Requirements

Each implementation must have tests for:

- valid config loading
- invalid config rejection
- SSH failed-password line parsing
- SSH brute-force threshold detection
- no event below threshold
- malformed lines do not crash detection
- SQLite event insertion and listing

Shared fixtures will live under:

```text
fixtures/
  logs/
  configs/
  expected-events/
```

## Benchmark Requirements

Each implementation must be benchmarked with the same inputs.

Required benchmark categories:

- startup time
- idle memory
- CPU usage while reading logs
- detection latency
- event insert throughput
- binary size
- shutdown time

Benchmark results must be saved under:

```text
benchmarks/results/
```

## Completion Criteria

ServerGuard v1 is complete when Go, Rust, and C++ all:

- pass the shared contract tests
- run the daemon against the same config and log fixtures
- detect the same SSH brute-force event
- store equivalent event rows in SQLite
- expose equivalent `status` and `events` CLI output fields
- have benchmark results recorded
- have a short security review note

No implementation should be judged before all three complete the same v1 milestone.
