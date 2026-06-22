<div align="center">

# 🛡️ ServerGuard

### Autonomous Server Guardian

**Detect threats. Protect your server. Self-improve over time.**

[![CI](https://github.com/serverguard-oss/serverguard/actions/workflows/ci.yml/badge.svg)](https://github.com/serverguard-oss/serverguard/actions)
[![PyPI version](https://img.shields.io/pypi/v/serverguard?color=green)](https://pypi.org/project/serverguard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-hardened-green)](SECURITY.md)

[Install](#install) · [Quick Start](#quick-start) · [Commands](#commands) · [Configuration](#configuration) · [Security](#security) · [Contributing](#contributing)

</div>

---

ServerGuard is a **Python-powered autonomous server guardian** that runs as a lightweight daemon on any Linux or macOS server. It monitors your system logs in real time, detects threats like SSH brute-force attacks, stores normalized security events, and will soon deliver alerts, take self-healing actions, and improve its threat model from experience.

Think of it as a security co-pilot for your server — always watching, always learning.

```
2026-06-22T10:15:20  WARNING  [security.ssh_bruteforce] 203.0.113.10
                              → 5 failed SSH attempts in 60s — BLOCKED
```

---

## Why ServerGuard?

| | ServerGuard | fail2ban | manual monitoring |
|---|---|---|---|
| Easy CLI setup | ✅ | ⚠️ complex config | ❌ |
| AI-ready architecture | ✅ | ❌ | ❌ |
| Tamper-evident audit log | ✅ | ❌ | ❌ |
| Self-improving threat model | ✅ (v0.1) | ❌ | ❌ |
| Notification anywhere | ✅ (v0.1) | ⚠️ | ❌ |
| Single Python install | ✅ | ❌ | ❌ |
| Hardened systemd service | ✅ | ⚠️ | ❌ |

---

## Install

**One line (Linux/macOS):**

```bash
curl -fsSL https://raw.githubusercontent.com/serverguard-oss/serverguard/main/scripts/install.sh | bash
```

**Or via pipx:**

```bash
pipx install serverguard
```

**Or via pip:**

```bash
pip install serverguard
```

Full installation guide: [docs/install.md](docs/install.md)

---

## Quick Start

**1. Create a config file:**

```toml
# /etc/serverguard/config.toml

[serverguard]
instance_id = "my-server"
data_dir    = "/var/lib/serverguard"

[[log_sources]]
name = "auth"
type = "ssh_auth"
path = "/var/log/auth.log"

[[detectors]]
name                     = "ssh_bruteforce"
enabled                  = true
source                   = "auth"
failed_attempt_threshold = 5
window_seconds           = 60
```

**2. Start the daemon:**

```bash
sgd --config /etc/serverguard/config.toml
```

**3. Check status and events (in another terminal):**

```bash
sg status --config /etc/serverguard/config.toml
sg events --config /etc/serverguard/config.toml
```

**4. Run as a system service:**

```bash
sudo cp packaging/serverguard.service /etc/systemd/system/
sudo systemctl enable --now serverguard
```

---

## Commands

| Command | Description |
|---|---|
| `sgd --config <path>` | Start the monitoring daemon (production) |
| `sgd --config <path> --replay` | Replay existing log content (testing/demo) |
| `sg status --config <path>` | Show daemon status, config summary |
| `sg events --config <path>` | List events (reverse chronological, color-coded) |
| `sg audit verify --config <path>` | Verify tamper-evident audit chain integrity |
| `sg --version` | Print version |

---

## Configuration

Full reference: [docs/configuration.md](docs/configuration.md)

Key config sections:

```toml
[serverguard]
instance_id = "prod-01"
data_dir    = "/var/lib/serverguard"

[security]
max_lines_per_second = 10000   # rate-limit protection

[[log_sources]]
name = "auth"
type = "ssh_auth"
path = "/var/log/auth.log"

[[detectors]]
name                     = "ssh_bruteforce"
enabled                  = true
source                   = "auth"
failed_attempt_threshold = 5
window_seconds           = 60
```

---

## Detectors

| Detector | Status | Description |
|---|---|---|
| `ssh_bruteforce` | ✅ v0.0.1 | Sliding-window failed SSH login counter with deduplication |
| `port_scan` | 🔜 v0.1.0 | Detect rapid connection attempts across ports |
| `anomaly_baseline` | 🔜 v0.2.0 | AI-powered rolling mean + σ anomaly scoring |

---

## Notifications (v0.1.0)

Send alerts anywhere when threats are detected:

| Channel | Status |
|---|---|
| Slack webhook | 🔜 v0.1.0 |
| Telegram bot | 🔜 v0.1.0 |
| Email (SMTP) | 🔜 v0.1.0 |
| Generic webhook | 🔜 v0.1.0 |
| Discord | 🔜 v0.1.0 |

Configure via environment variables — no secrets in config files:

```bash
export SERVERGUARD_TELEGRAM_BOT_TOKEN="123:abc..."
export SERVERGUARD_TELEGRAM_CHAT_ID="-100123..."
```

---

## Security

ServerGuard is built with defense-in-depth to protect the machines it runs on:

| Layer | Implementation |
|---|---|
| **Input sanitization** | All log lines length-bounded (4 KiB), control chars stripped, null bytes rejected |
| **Rate limiting** | 10,000 lines/sec per source cap — prevents log flooding exhausting CPU/RAM |
| **Tamper-evident audit** | SHA-256 hash-chained audit table; verify with `sg audit verify` |
| **Config permissions** | Warns if world-readable config or world-writable data dir |
| **Least privilege** | Runs as dedicated `serverguard` system user (not root) |
| **Systemd hardening** | `NoNewPrivileges`, `ProtectSystem=strict`, syscall filtering, memory limits |
| **No telemetry** | Zero outbound connections — all data stays on your server |
| **Minimal deps** | Small attack surface; all dependencies pinned and audited in CI |

Security policy & responsible disclosure: [SECURITY.md](SECURITY.md)

---

## Roadmap

| Version | Features |
|---|---|
| **v0.0.1** | SSH brute-force detection, CLI, tamper-evident audit log, security hardening |
| **v0.1.0** | Slack/Telegram/Email/Webhook notifications, port scan detector, log rotation |
| **v0.2.0** | Self-healing actions (auto-ban IPs via iptables/ufw), AI anomaly baseline |
| **v0.3.0** | `sg learn` custom detection patterns, per-IP threat memory, `sg schedule` routines |
| **v1.0.0** | Stable API, multi-server dashboard, plugin system |

---

## Development

```bash
git clone https://github.com/serverguard-oss/serverguard
cd serverguard

make install-dev   # creates .venv + installs deps
make test          # 44 tests — unit + contract
make lint          # ruff check
make run-daemon    # demo against shared fixture
```

---

## Contributing

All contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 [Report a bug](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 [Request a feature](.github/ISSUE_TEMPLATE/feature_request.md)
- 🔒 [Report a security issue](SECURITY.md) (private)

---

## License

[MIT](LICENSE) © 2026 ServerGuard Contributors
