<div align="center">

<img src="image/image.png" alt="ServerGuard" width="600"/>

### Autonomous Server Guardian

**Detect threats. Get alerts. Self-improve. Protect your server 24/7.**

[![CI](https://github.com/AdityaKumar41/serverguard-oss/actions/workflows/ci.yml/badge.svg)](https://github.com/AdityaKumar41/serverguard-oss/actions)
[![PyPI version](https://img.shields.io/pypi/v/serverguard?color=green)](https://pypi.org/project/serverguard/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-hardened-green)](SECURITY.md)

[Install](#install) · [Setup](#quick-start) · [Commands](#commands) · [AI Features](#ai-features) · [Notifications](#notifications) · [Security](#security-architecture) · [Contributing](#contributing)

</div>

---

ServerGuard is a **Python-powered autonomous server guardian** — a single CLI that monitors your Linux server in real time, detects SSH brute-force attacks (and more), sends instant alerts to Telegram/Discord/Slack/Email, uses AI to explain and contextualize every threat, and quietly improves its own detection thresholds from experience.

Set it up in 60 seconds. Run it forever.

```
$ sgd --config ~/.serverguard/config.toml

2026-06-22T20:15:37  INFO    Daemon started — watching 1 log source(s)
2026-06-22T20:15:37  WARNING [security.ssh_bruteforce] 203.0.113.10
                             → 5 failed SSH attempts in 60s — ALERT SENT

→ Telegram: 🔴 SSH brute-force detected
   📍 IP Location: Shanghai, China (Alibaba Cloud)
   🤖 AI Analysis: Automated credential stuffing attack from known hosting
                   range. Recommend: ufw deny from 203.0.113.10 to any port 22
```

---

## Why ServerGuard?

| | ServerGuard | fail2ban | manual watching |
|---|---|---|---|
| One-command setup | ✅ `sg setup` | ❌ complex config | ❌ |
| AI threat summaries | ✅ | ❌ | ❌ |
| IP geolocation per alert | ✅ | ❌ | ❌ |
| Self-improving thresholds | ✅ | ❌ | ❌ |
| Telegram / Discord / Slack | ✅ | ❌ | ❌ |
| Tamper-evident audit log | ✅ | ❌ | ❌ |
| Ask AI about your server | ✅ `sg ask` | ❌ | ❌ |
| Hot-swap AI providers | ✅ `sg model` | ❌ | ❌ |
| Hardened systemd unit | ✅ | ⚠️ | ❌ |

---

## Install

**One line:**

```bash
curl -fsSL https://raw.githubusercontent.com/AdityaKumar41/serverguard-oss/main/scripts/install.sh | bash
```

**Or via pipx (recommended):**

```bash
pipx install serverguard
```

**Or via pip:**

```bash
pip install serverguard
```

Requires Python 3.11+. Works on Ubuntu, Debian, RHEL/CentOS, Fedora, and macOS.

---

## Quick Start

### Step 1 — Run the setup wizard

```bash
sg setup
```

The wizard walks you through:

1. **AI Model Provider** — OpenAI, Anthropic, OpenRouter, Ollama (local/free), or skip
2. **Notification Channels** — Telegram, Discord, Slack, Webhook, Email (add multiple)
3. **Log Sources** — auto-detected from your system (`/var/log/auth.log`, etc.)
4. **Instance Name** — your server's name in alerts

Everything is saved to `~/.serverguard/config.toml`. API keys go in `~/.serverguard/.env` (never in the TOML).

### Step 2 — Start the daemon

```bash
sgd --config ~/.serverguard/config.toml
```

### Step 3 — Check status

```bash
sg status --config ~/.serverguard/config.toml
sg events --config ~/.serverguard/config.toml
```

### Step 4 — Run as a system service

```bash
sudo cp packaging/serverguard.service /etc/systemd/system/
sudo systemctl enable --now serverguard
```

---

## Commands

### Core

| Command | Description |
|---|---|
| `sg setup` | Interactive setup wizard (AI + notifications + log sources) |
| `sg status --config <path>` | Show daemon status, config, recent event counts |
| `sg events --config <path>` | List events, reverse-chronological, color-coded severity |
| `sgd --config <path>` | Start the monitoring daemon |
| `sgd --config <path> --replay` | Replay existing log content (testing/demo) |

### AI

| Command | Description |
|---|---|
| `sg ask --config <path> "question"` | Ask AI anything about your server's security |
| `sg model` | Interactive AI provider switcher |
| `sg model set openai gpt-4o` | Set provider non-interactively |
| `sg model set ollama llama3.2` | Switch to local Ollama (free, no API key) |
| `sg model list` | List all supported providers and models |

### Security

| Command | Description |
|---|---|
| `sg audit verify --config <path>` | Verify tamper-evident audit chain integrity |
| `sg --version` | Print version |

---

## AI Features

ServerGuard integrates AI at every layer — not as a gimmick, but to make server security actually understandable.

### 1. Instant Threat Summaries

Every security event gets an AI-generated plain-English explanation:

```
🤖 AI Analysis: Automated credential stuffing attack from known cloud
   hosting range. No successful logins observed. Recommended action:
   ufw deny from 203.0.113.10 to any port 22
```

### 2. IP Geolocation & Reputation

Every attacker IP is automatically enriched:

```
🌍 IP Location: Shanghai, China (Alibaba Cloud)
   ⚠️  Hosting provider (common bot origin)
```

### 3. Self-Learning Loop

After accumulating 10 events of the same type, ServerGuard:
- Analyzes the pattern with AI
- Recommends tightening detection thresholds
- Saves the suggestion to `~/.serverguard/data/learned_suggestions.json`
- Logs it as a `learning.suggestion` event

### 4. AI Q&A (`sg ask`)

Ask anything about your server's security history in plain English:

```bash
sg ask --config ~/.serverguard/config.toml "Am I under attack right now?"
sg ask --config ~/.serverguard/config.toml "Which IP has hit me the most?"
sg ask --config ~/.serverguard/config.toml "Should I block the 203.0.113.0/24 range?"
```

### Supported AI Providers

| Provider | Models | Setup |
|---|---|---|
| **OpenAI** | GPT-4o, GPT-4o-mini | `OPENAI_API_KEY` |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Haiku | `ANTHROPIC_API_KEY` |
| **OpenRouter** | 200+ models (one key) | `OPENROUTER_API_KEY` |
| **Ollama** | llama3.2, mistral, gemma3 (local, free) | None needed |

Switch providers anytime without restarting: `sg model set ollama llama3.2`

---

## Notifications

Configure during `sg setup` or add manually to `config.toml`.

### Telegram (Recommended)

Get alerts on your phone instantly. Also supports bot commands (`/status`, `/events`, `/ask`).

```bash
# 1. Create a bot: message @BotFather → /newbot → copy token
# 2. Set env vars (in ~/.serverguard/.env):
SERVERGUARD_TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
SERVERGUARD_TELEGRAM_CHAT_ID=-100123456789
```

```toml
# In config.toml:
[[notifiers]]
type    = "telegram"
enabled = true
```

**What a Telegram alert looks like:**
```
🔴 ServerGuard Alert

Type: security.ssh_bruteforce
Severity: WARNING
Subject: 203.0.113.10
Time: 2026-06-22T20:15:37

5 failed SSH attempts from 203.0.113.10 within 60s

🤖 AI Analysis: Automated attack from cloud VPS...
🌍 IP Location: Shanghai, China (Alibaba Cloud)
```

### Discord

```bash
SERVERGUARD_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Slack

```bash
SERVERGUARD_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Email (SMTP)

```bash
SERVERGUARD_SMTP_HOST=smtp.gmail.com
SERVERGUARD_SMTP_PORT=587
SERVERGUARD_SMTP_USER=alerts@example.com
SERVERGUARD_SMTP_PASSWORD=your-app-password
SERVERGUARD_SMTP_TO=ops@example.com
```

### Custom Webhook (HMAC-signed)

```bash
SERVERGUARD_WEBHOOK_URL=https://your-service.com/hook
SERVERGUARD_WEBHOOK_SECRET=your-signing-secret  # optional
```

---

## Detectors

| Detector | Status | Description |
|---|---|---|
| `ssh_bruteforce` | ✅ v0.0.1 | Sliding-window failed SSH login counter |
| `port_scan` | 🔜 v0.1.0 | Rapid port sweep detection |
| `anomaly_baseline` | 🔜 v0.2.0 | AI-powered rolling anomaly scoring |

---

## Security Architecture

ServerGuard uses defense-in-depth. It guards itself as fiercely as it guards your server.

| Layer | Implementation |
|---|---|
| **Input sanitization** | All log lines bounded at 4 KiB, null bytes stripped, control chars removed |
| **Rate limiting** | 10,000 lines/sec/source cap — prevents CPU/RAM exhaustion from log flooding |
| **Tamper-evident audit** | SHA-256 hash-chained `audit_chain` table — verify with `sg audit verify` |
| **Config permissions** | Warns if config is world-readable or data dir is world-writable |
| **Least privilege** | Dedicated `serverguard` system user; root usage warned loudly |
| **Hardened systemd** | `NoNewPrivileges`, `ProtectSystem=strict`, syscall whitelist, memory limit |
| **Secrets in env only** | No API keys in config files, ever |
| **Zero telemetry** | No outbound connections except configured notifiers and your AI provider |
| **Minimal dependencies** | Small attack surface; all deps pinned and audited in CI |

---

## Configuration Reference

```toml
[serverguard]
instance_id = "prod-web-01"
data_dir    = "~/.serverguard/data"

[security]
max_lines_per_second = 10000

[ai]
provider = "openai"       # openai | anthropic | openrouter | ollama | disabled
model    = "gpt-4o"

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

[[notifiers]]
type    = "telegram"
enabled = true

[[notifiers]]
type    = "discord"
enabled = true
```

Full reference: [docs/configuration.md](docs/configuration.md)

---

## Roadmap

| Version | Features |
|---|---|
| **v0.0.1** | SSH brute-force, AI summaries + geo, Telegram/Discord/Slack/Email, setup wizard, `sg ask`, self-learning loop, tamper-evident audit, security hardening |
| **v0.1.0** | Port scan detector, log rotation, gateway bot (`/status` from Telegram), `sg gateway telegram` |
| **v0.2.0** | Self-healing actions (`ufw` / `iptables` auto-ban), AI anomaly baseline, `sg schedule` cron routines |
| **v0.3.0** | Multi-server dashboard, plugin system, `sg learn` custom patterns |
| **v1.0.0** | Stable API, Windows PTY support, enterprise features |

---

## Development

```bash
git clone https://github.com/AdityaKumar41/serverguard-oss
cd serverguard-oss

make install-dev    # creates .venv + installs all dev deps
make test           # 44+ tests (unit + contract)
make lint           # ruff check
make run-daemon     # demo against shared fixture (detects brute-force)
make run-events     # show events from the demo run
```

See [AGENTS.md](AGENTS.md) for the full developer guide: architecture, contribution rubric, footprint ladder, security checklist, and step-by-step guides for adding detectors/notifiers/AI providers.

---

## Contributing

All contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

- 🐛 [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)
- 🔒 [Security issue](SECURITY.md) (private disclosure)
- 📖 [Developer guide](AGENTS.md)

---

## License

[MIT](LICENSE) © 2026 ServerGuard Contributors
