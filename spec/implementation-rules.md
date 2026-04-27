# ServerGuard Implementation Rules

## Purpose

These rules keep the Go, Rust, and C++ implementations readable, comparable, and easy to review.

## File Size

- Source code files must stay at or below 100 physical lines.
- Split files by responsibility before crossing the limit.
- Generated files are exempt, but generated code must not be hand-edited.

## Code Shape

- Prefer small functions with one clear job.
- Keep parsing, detection, storage, and CLI rendering in separate modules.
- Avoid clever abstractions until two implementations prove the pattern is useful.
- Optimize hot paths, but only after correctness tests exist.

## Comments

- Add comments for intent, invariants, and non-obvious tradeoffs.
- Do not comment obvious assignments or syntax.
- Every detector should explain the rule it implements near the matching logic.

## Error Handling

- Return clear errors for invalid config, missing files, and database failures.
- Never silently drop security events.
- Malformed log lines must not crash the daemon.

## Testing

- Add tests before production behavior when implementation code begins.
- Every implementation must pass the shared fixtures before benchmarks matter.
- Contract tests should compare logical event fields, not generated IDs or timestamps.

## Performance

- Avoid rereading already processed log lines during one daemon run.
- Keep metadata construction bounded to the matched detection window.
- Measure startup, memory, CPU, detection latency, SQLite writes, binary size, and shutdown time with shared inputs.
