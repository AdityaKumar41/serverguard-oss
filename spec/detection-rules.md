# ServerGuard Detection Rules

## Purpose

This document defines the shared v1 detection behavior.

The first detector is intentionally narrow so the Go, Rust, and C++ implementations can be compared on the same problem.

## Supported Detector

Supported in v1:

- `ssh_bruteforce`

## Input

The detector consumes lines from a configured log source of type `ssh_auth`.

Example matching lines:

```text
Apr 25 10:15:01 host sshd[1234]: Failed password for invalid user admin from 203.0.113.10 port 54321 ssh2
Apr 25 10:15:03 host sshd[1235]: Failed password for root from 203.0.113.10 port 54322 ssh2
```

## Minimum Parsed Fields

Each implementation must extract at least:

- timestamp text from the log line
- username when present
- source IP address
- source port when present
- raw line

## Detection Rule

Emit one `security.ssh_bruteforce` event when the same source IP reaches at least `failed_attempt_threshold` failed SSH password attempts within `window_seconds`.

## Deduplication Rule

After an implementation emits a `security.ssh_bruteforce` event for an IP address, it must not emit another event for that same IP address until a new failed attempt arrives outside the previous detection window.

## Non-Matching Input

The detector must:

- ignore unrelated log lines
- ignore malformed lines
- keep running after parse failures
- avoid crashing the daemon because of bad input

## Log Watching Constraints

For v1, implementations may poll the file instead of using platform-specific file event APIs.

The watcher must:

- read new lines from the configured file
- avoid rereading already processed lines during one daemon run
- tolerate empty files
- produce a clear startup error if the file does not exist

Log rotation support is out of scope for v1.
