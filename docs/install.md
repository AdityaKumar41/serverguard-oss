# Installation

ServerGuard requires **Python 3.11+**. It runs on Linux and macOS.

---

## One-Line Install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/serverguard-oss/serverguard/main/scripts/install.sh | bash
```

This installs `sg` and `sgd` via `pipx` (isolated environment, no system Python pollution).

---

## Install via pipx (Recommended)

```bash
pip install pipx
pipx install serverguard
```

---

## Install via pip

```bash
pip install serverguard
```

---

## Install from Source

```bash
git clone https://github.com/serverguard-oss/serverguard
cd serverguard
make install-dev    # creates .venv and installs all dependencies
```

---

## Production Setup (Linux Server)

### 1. Create a dedicated system user

```bash
sudo useradd -r -s /bin/false -d /var/lib/serverguard serverguard
sudo mkdir -p /var/lib/serverguard /etc/serverguard
sudo chown serverguard:serverguard /var/lib/serverguard
```

### 2. Install ServerGuard

```bash
sudo pip install serverguard
# or
sudo pipx install serverguard --global
```

### 3. Create a config file

```bash
sudo cp /etc/serverguard/config.toml.example /etc/serverguard/config.toml
sudo nano /etc/serverguard/config.toml
sudo chmod 600 /etc/serverguard/config.toml
sudo chown serverguard:serverguard /etc/serverguard/config.toml
```

### 4. Enable the systemd service

```bash
sudo cp packaging/serverguard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now serverguard
sudo systemctl status serverguard
```

### 5. Verify

```bash
sg status --config /etc/serverguard/config.toml
sg events --config /etc/serverguard/config.toml
```

---

## Verify the Audit Chain

After the daemon has run, verify the tamper-evident audit log:

```bash
sg audit verify --config /etc/serverguard/config.toml
```

If the chain is intact, you'll see: `✅ Audit chain verified — N records, no tampering detected.`

---

## Uninstall

```bash
pipx uninstall serverguard
# or
pip uninstall serverguard
```
