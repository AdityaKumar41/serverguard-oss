# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.0.x   | ✅ Yes    |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

ServerGuard handles sensitive server data — responsible disclosure is critical.

### How to Report

1. Go to **[GitHub Security Advisories](https://github.com/AdityaKumar41/serverguard-oss/security/advisories/new)**
2. Submit a private advisory with:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fix (optional)

We will acknowledge your report within **48 hours** and provide a timeline for a fix within **7 days**.

### What to Report

- Remote code execution, privilege escalation, or authentication bypass
- Injection vulnerabilities (log injection, SQL injection, path traversal)
- Denial-of-service vulnerabilities in the daemon
- Data exposure from the SQLite event store
- Insecure defaults that could harm production deployments
- Supply chain issues (compromised dependency)

### What is Out of Scope

- Vulnerabilities in systems that ServerGuard monitors (not our responsibility)
- Theoretical attacks with no realistic exploit path
- Issues already documented in `CHANGELOG.md` as known limitations

## Disclosure Policy

- We follow [coordinated disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure)
- We will credit reporters in the release notes (unless they prefer anonymity)
- Security fixes will be released as patch versions (e.g., 0.0.2) as soon as possible

## Security Design Principles

ServerGuard is designed with defense-in-depth:

- **Input sanitization** — all log lines are length-bounded and control-char stripped before parsing
- **Rate limiting** — max 10,000 lines/sec per source to prevent log flooding
- **Least privilege** — daemon recommends running as a dedicated `serverguard` system user
- **Tamper-evident audit log** — SHA-256 hash-chained audit trail, verifiable with `sg audit verify`
- **Config hardening** — warns on world-readable config or world-writable data directory
- **No outbound telemetry** — ServerGuard never phones home; all data stays on your server
- **Minimal dependencies** — small attack surface, all dependencies pinned and audited in CI
