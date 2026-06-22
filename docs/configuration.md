# Configuration Reference

ServerGuard uses [TOML](https://toml.io) for configuration.

---

## Example Config

```toml
[serverguard]
instance_id = "prod-web-01"
data_dir    = "/var/lib/serverguard"

[security]
max_lines_per_second = 10000   # rate limit per log source

[[log_sources]]
name = "auth"
type = "ssh_auth"
path = "/var/log/auth.log"     # Linux
# path = "/var/log/secure"     # RHEL/CentOS

[[log_sources]]
name = "syslog"
type = "ssh_auth"
path = "/var/log/syslog"

[[detectors]]
name    = "ssh_bruteforce"
enabled = true
source  = "auth"
failed_attempt_threshold = 5
window_seconds           = 60
```

---

## `[serverguard]`

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `instance_id` | string | ✅ | Unique name for this server instance. Used in event `subject` for audit events. |
| `data_dir` | string | ✅ | Directory where ServerGuard stores its SQLite database and state. Will be created if absent. |

---

## `[security]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_lines_per_second` | integer | `10000` | Maximum log lines per second per source before rate limiting kicks in. Protects against log flooding. |

---

## `[[log_sources]]`

Define one or more log sources to monitor. Each `[[log_sources]]` block is one source.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | ✅ | Unique source name. Used in event `source` field and referenced by detectors. |
| `type` | string | ✅ | Parser type. Currently supported: `ssh_auth` |
| `path` | string | ✅ | Absolute path to the log file. |

### Supported Types

| Type | Log File | Detects |
|------|----------|---------|
| `ssh_auth` | `/var/log/auth.log` (Debian/Ubuntu) or `/var/log/secure` (RHEL/CentOS) | SSH brute-force, invalid users |

---

## `[[detectors]]`

Define one detector per block.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | ✅ | Unique detector name. Must match a known detector type. |
| `enabled` | boolean | ✅ | Set to `false` to disable without removing the config. |
| `source` | string | ✅ | The `name` of the `[[log_sources]]` block to monitor. |
| `failed_attempt_threshold` | integer | ✅ (ssh_bruteforce) | Number of failed attempts to trigger detection. |
| `window_seconds` | integer | ✅ (ssh_bruteforce) | Time window in seconds for counting attempts. |

---

## Config File Security

ServerGuard warns at startup if:

- The config file is **world-readable** (mode should be `600` or `640`)
- The data directory is **world-writable**
- The daemon is running as **root** (use a dedicated `serverguard` user)

Recommended permissions:

```bash
chmod 600 /etc/serverguard/config.toml
chown serverguard:serverguard /etc/serverguard/config.toml
```

---

## Environment Variables

Sensitive values (API keys for notifications) must never go in the config file. Use environment variables or a `.env` file:

```bash
SERVERGUARD_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SERVERGUARD_TELEGRAM_BOT_TOKEN=123456:ABC...
SERVERGUARD_TELEGRAM_CHAT_ID=-100123456789
```

See `.env.example` for all supported variables.
