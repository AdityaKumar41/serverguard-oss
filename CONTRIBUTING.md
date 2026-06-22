# Contributing to ServerGuard

Thank you for your interest in contributing! ServerGuard is an open-source project and welcomes contributions of all kinds — bug fixes, new detectors, notification integrations, documentation, and more.

## Development Setup

```bash
git clone https://github.com/serverguard-oss/serverguard
cd serverguard

# Create a virtualenv and install all dev dependencies
make install-dev

# Run the full test suite
make test

# Lint
make lint
```

**Requirements:** Python 3.11+

## Making Changes

### Branch Naming

- `fix/<description>` — bug fixes
- `feat/<description>` — new features
- `docs/<description>` — documentation only
- `security/<description>` — security fixes (consider private disclosure first — see SECURITY.md)

### Code Standards

- Files must stay at or below **150 lines** (split by responsibility when approaching the limit)
- All functions must have a docstring explaining intent
- New detectors must live in `serverguard/detectors/` and extend `Detector` base class
- New notifiers must live in `serverguard/notifiers/` and extend `Notifier` base class
- No secrets, tokens, or API keys in code or tests — use `os.environ` + `.env.example`

### Tests

- Every new feature must include at least one unit test
- Every new detector must include a contract test against a log fixture
- All tests must pass before a PR can be merged: `make test`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(detector): add port scan detection
fix(storage): handle concurrent insert failure gracefully
docs(readme): update installation instructions
security(input): tighten log line length limit
```

### DCO Sign-Off

All commits require a Developer Certificate of Origin sign-off:

```bash
git commit -s -m "feat: your change"
```

This certifies you have the right to submit the contribution under the MIT License.

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. Make your changes following the standards above
3. Run `make test` and `make lint` — both must pass
4. Open a PR with a clear description of what and why
5. A maintainer will review within 7 days
6. Address review comments, then the PR will be merged

## Reporting Bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

Include:
- Your OS and Python version
- The exact command that failed
- The full error output
- Your config file (redact any secrets)

## Requesting Features

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

Before opening a request, search existing issues to avoid duplicates.

## Security Issues

**Do not open public issues for security vulnerabilities.**
See [SECURITY.md](SECURITY.md) for private disclosure instructions.

## Code of Conduct

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
