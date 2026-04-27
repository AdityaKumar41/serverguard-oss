# ServerGuard Research Charter

## Goal

Build ServerGuard in Go, Rust, and C++ from one shared product specification, then compare the implementations using measurable engineering, performance, security, and operational criteria.

The purpose is not to guess which language is best. The purpose is to produce evidence by building the same product shape three times under the same rules.

## Core Rule

There is one ServerGuard specification and three implementations.

The implementations must follow the same behavior, command names, configuration format, event format, database schema, test fixtures, and benchmark inputs. A language implementation may choose idiomatic internal architecture, but it must not change the user-visible product behavior.

## Implementations

- `serverguard-go`
- `serverguard-rust`
- `serverguard-cpp`

## Repository Strategy

ServerGuard will use a monorepo during the research phase. Shared specifications, fixtures, benchmarks, and reports will live next to the three implementations so every language is measured against the same source of truth.

Proposed structure:

```text
serverguard/
  docs/
    plans/
    decisions/
    reports/

  spec/
    serverguard-v1.md
    cli.md
    config.md
    events.md
    database.md
    detection-rules.md

  fixtures/
    logs/
    configs/
    expected-events/

  implementations/
    go/
    rust/
    cpp/

  benchmarks/
    runner/
    results/
```

## Phase Targets

### Phase 0: Research Foundation

Create the project structure, research charter, and first shared specification outline.

Success means the project has a clear goal, agreed comparison rules, and a stable place for specs, fixtures, implementations, benchmarks, and reports.

### Phase 1: Shared Specification

Define the first ServerGuard vertical slice in language-neutral terms.

The first slice should include daemon lifecycle, configuration loading, log watching, SSH brute-force detection, event format, local event storage, and basic CLI status commands.

Success means Go, Rust, and C++ can all implement the same written behavior without guessing.

### Phase 2: Shared Fixtures and Contract Tests

Create common input files and expected outputs.

This includes sample logs, sample configs, expected detection events, and contract test rules that all three implementations must satisfy.

Success means each implementation can be tested against the same fixtures.

### Phase 3: Minimal Daemon

Build a minimal daemon in Go, Rust, and C++.

Each daemon must start, load config, expose health/status, handle shutdown, and write a basic audit event.

Success means all three implementations can run as long-lived processes with the same lifecycle behavior.

### Phase 4: Log Watcher and SSH Brute-Force Detector

Implement the first real detector in all three languages.

Each implementation must watch the same fixture log stream, detect the same SSH brute-force pattern, and emit the same normalized event.

Success means detection behavior is equivalent across all three languages.

### Phase 5: SQLite Event Storage

Store normalized events in a shared SQLite schema.

Success means all three implementations write equivalent event records and the CLI can read them consistently.

### Phase 6: CLI Status and Event Listing

Build the first CLI commands.

Required commands:

- `sg status`
- `sg events`

Success means the CLI behavior and output fields are equivalent across all three implementations.

### Phase 7: Benchmarks

Run the same benchmark suite against Go, Rust, and C++.

Measure startup time, idle memory, memory under load, CPU under load, detection latency, SQLite write throughput, binary size, and shutdown time.

Success means results are reproducible and recorded in `benchmarks/results/`.

### Phase 8: Security Review

Review each implementation for security posture.

Measure memory safety, unsafe code usage, dependency risk, malformed input behavior, privilege boundaries, audit logging, and failure behavior.

Success means every implementation has a written security assessment.

### Phase 9: Decision Report

Compare results and decide how to continue.

Possible outcomes:

- continue all three
- select one primary implementation
- select one primary implementation plus one specialized secondary implementation
- pause or abandon one or more implementations

No implementation will be abandoned until all three complete the same milestone and the benchmark and review data for that milestone is recorded.

## Comparison Criteria

### Correctness

- passes shared contract tests
- emits expected events
- handles shutdown correctly
- preserves audit history

### Runtime Efficiency

- startup time
- idle memory
- memory under load
- CPU under load
- detection latency
- SQLite write throughput
- binary size

### Engineering Cost

- implementation time
- code complexity
- test complexity
- dependency count
- build complexity
- packaging complexity
- cross-platform friction

### Security Posture

- memory safety
- unsafe code usage
- malformed input handling
- dependency attack surface
- privilege handling
- audit log reliability
- crash behavior

### Operational Quality

- clear logs
- stable daemon behavior
- predictable configuration errors
- clean upgrades
- useful CLI output
- ease of debugging production issues

## Decision Rules

No language wins because of preference.

No language loses because of reputation.

Each decision must reference measured results, implementation experience, security review notes, and maintenance expectations.

If one implementation is ahead, the reason must be recorded. If one implementation falls behind, the reason must be recorded. This keeps the comparison honest.

## Initial Hypotheses

These are starting assumptions, not conclusions.

- Go may provide the best product development speed and operational simplicity.
- Rust may provide the best memory safety and low-level performance profile.
- C++ may provide strong performance but require the most discipline around safety and maintenance.

The project exists to test these assumptions with evidence.
