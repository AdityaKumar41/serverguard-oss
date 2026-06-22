---
name: Bug Report
about: Report a bug or unexpected behavior in ServerGuard
title: "[BUG] "
labels: ["bug", "needs-triage"]
assignees: []
---

## Describe the Bug

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Start daemon with `sgd --config ...`
2. Run command `sg ...`
3. Observe error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened. Include the full error output.

```
paste error output here
```

## Environment

- **OS:** (e.g., Ubuntu 22.04, macOS 14, Debian 12)
- **Python version:** (e.g., 3.11.9) — run `python3 --version`
- **ServerGuard version:** (e.g., 0.0.1) — run `sg --version`

## Config File

Paste your config (redact any API keys or sensitive values):

```toml
[serverguard]
instance_id = "..."
# ...
```

## Additional Context

Any other context about the problem here. Logs, screenshots, etc.

---

> [!IMPORTANT]
> For security vulnerabilities, do NOT open a public issue. See [SECURITY.md](../../SECURITY.md).
