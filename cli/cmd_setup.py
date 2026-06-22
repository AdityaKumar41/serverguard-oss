"""sg setup — interactive setup wizard.

Guides the user through connecting an AI model provider, configuring
notification channels, and auto-detecting log sources on the system.

Guides the user through:
  1. Choosing an AI model provider and entering their API key
  2. Configuring notification channels (Telegram, Discord, Slack, etc.)
  3. Auto-detecting log sources on the local system
  4. Naming the server instance

Writes a complete config.toml and .env file to ~/.serverguard/.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

console = Console()

# ── Defaults ──────────────────────────────────────────────────────────────────

SG_HOME = Path.home() / ".serverguard"
DEFAULT_CONFIG = SG_HOME / "config.toml"
DEFAULT_ENV = SG_HOME / ".env"

# Auto-detect common log file paths (Linux + macOS)
_CANDIDATE_LOG_PATHS = [
    ("/var/log/auth.log", "ssh_auth", "Ubuntu/Debian SSH auth log"),
    ("/var/log/secure", "ssh_auth", "RHEL/CentOS/Fedora SSH auth log"),
    ("/var/log/syslog", "ssh_auth", "General syslog (Debian/Ubuntu)"),
    ("/var/log/messages", "ssh_auth", "General syslog (RHEL/CentOS)"),
]

_PROVIDER_CHOICES = {
    "1": ("openai", "OpenAI (GPT-4o, GPT-4o-mini)", "OPENAI_API_KEY"),
    "2": ("anthropic", "Anthropic (Claude 3.5 Sonnet, Claude Haiku)", "ANTHROPIC_API_KEY"),
    "3": ("openrouter", "OpenRouter (200+ models, one API key)", "OPENROUTER_API_KEY"),
    "4": ("opencode", "OpenCode (open-source agent, free tier)", "OPENCODE_API_KEY"),
    "5": ("groq", "Groq (ultra-fast, generous free tier)", "GROQ_API_KEY"),
    "6": ("mistral", "Mistral AI (mistral-large, codestral)", "MISTRAL_API_KEY"),
    "7": ("together", "Together AI (open-source models)", "TOGETHER_API_KEY"),
    "8": ("ollama", "Ollama (local, completely free \u2014 no API key)", None),
    "9": ("disabled", "Skip \u2014 no AI features", None),
}

_NOTIFIER_CHOICES = {
    "1": "telegram",
    "2": "discord",
    "3": "slack",
    "4": "webhook",
    "5": "email",
    "6": "skip",
}


def run() -> None:
    """Full interactive setup wizard."""
    _print_banner()

    SG_HOME.mkdir(parents=True, exist_ok=True)

    console.print("\n[bold]Welcome to ServerGuard v0.0.1 setup![/]\n")
    console.print("This wizard will configure your server guardian in 4 steps.\n")

    # ── Step 1: AI Provider ───────────────────────────────────────────────────
    console.print(Rule("[bold cyan]Step 1 / 4 \u2014 AI Model Provider[/]"))
    console.print(
        "\nServerGuard uses AI to summarize incidents, enrich threat context,\n"
        "and self-improve its detection thresholds over time.\n"
    )

    _print_choices(_PROVIDER_CHOICES, "AI Provider")
    provider_choice = Prompt.ask("Your choice", choices=list(_PROVIDER_CHOICES), default="9")
    provider_id, provider_label, env_var = _PROVIDER_CHOICES[provider_choice]

    api_key = ""
    model = ""
    if env_var:
        existing = os.environ.get(env_var, "")
        if existing:
            console.print(f"  \u2705 Found existing {env_var} in environment")
            api_key = existing
        else:
            api_key = Prompt.ask(f"  {env_var}", password=True, default="")
    elif provider_id == "ollama":
        console.print("  \u2705 Ollama runs locally \u2014 no API key needed")
        console.print("  Make sure Ollama is running: [dim]ollama serve[/]")

    if provider_id != "disabled":
        from agent.providers import PROVIDER_MODELS, ProviderName

        try:
            pname = ProviderName(provider_id)
            available = PROVIDER_MODELS.get(pname, [])
        except ValueError:
            available = []

        if available:
            console.print(f"\n  Available models: {', '.join(available[:4])}")
            model = Prompt.ask("  Model", default=available[0])

    console.print()

    # ── Step 2: Notification Channels ────────────────────────────────────────
    console.print(Rule("[bold cyan]Step 2 / 4 \u2014 Notification Channels[/]"))
    console.print(
        "\nServerGuard delivers incident alerts to your preferred channels.\n"
        "You can add multiple channels.\n"
    )

    notifier_configs: list[dict] = []
    env_additions: dict[str, str] = {}

    while True:
        _print_notifier_choices()
        choice = Prompt.ask(
            "Add channel (or 6 to continue)", choices=["1", "2", "3", "4", "5", "6"], default="6"
        )
        if choice == "6":
            break

        ntype = _NOTIFIER_CHOICES[choice]
        cfg, env = _configure_notifier(ntype)
        if cfg:
            notifier_configs.append(cfg)
            env_additions.update(env)
            console.print(f"  \u2705 {ntype.capitalize()} channel added\n")

    console.print()

    # ── Step 3: Log Sources ───────────────────────────────────────────────────
    console.print(Rule("[bold cyan]Step 3 / 4 \u2014 Log Sources[/]"))
    console.print("\nScanning for log files on this system...\n")

    detected_sources = []
    for path, ltype, desc in _CANDIDATE_LOG_PATHS:
        if os.path.exists(path):
            console.print(f"  \u2705 [green]{path}[/] \u2014 {desc}")
            detected_sources.append({"name": Path(path).stem, "path": path, "type": ltype})
        else:
            console.print(f"  [dim]\u2212 {path} (not found)[/]")

    if not detected_sources:
        console.print("\n  [yellow]No standard log files found.[/]")
        custom = Prompt.ask("  Enter path to your SSH/auth log", default="")
        if custom and os.path.exists(custom):
            detected_sources.append({"name": "auth", "path": custom, "type": "ssh_auth"})

    console.print()

    # ── Step 4: Instance Name ─────────────────────────────────────────────────
    console.print(Rule("[bold cyan]Step 4 / 4 \u2014 Instance Name[/]"))
    default_name = platform.node() or "my-server"
    instance_id = Prompt.ask("\n  Server name", default=default_name)
    console.print()

    # ── Write config ──────────────────────────────────────────────────────────
    _write_config(
        instance_id=instance_id,
        provider_id=provider_id,
        model=model,
        log_sources=detected_sources,
        notifier_configs=notifier_configs,
    )
    _write_env(api_key=api_key, env_var=env_var, extras=env_additions)

    # ── Done ──────────────────────────────────────────────────────────────────
    console.print(
        Panel(
            f"[bold green]\u2705 Setup complete![/]\n\n"
            f"Config written to: [cyan]{DEFAULT_CONFIG}[/]\n"
            f"Secrets stored in: [cyan]{DEFAULT_ENV}[/]\n\n"
            f"[bold]Start the daemon:[/]\n"
            f"  [dim]sgd --config {DEFAULT_CONFIG}[/]\n\n"
            f"[bold]Check status:[/]\n"
            f"  [dim]sg status --config {DEFAULT_CONFIG}[/]\n\n"
            f"[bold]View events:[/]\n"
            f"  [dim]sg events --config {DEFAULT_CONFIG}[/]",
            title="\U0001f6e1\ufe0f  ServerGuard Ready",
            border_style="green",
        )
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _print_banner() -> None:
    console.print()
    console.print(
        "[bold cyan]"
        "  \u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \n"  # noqa: E501
        "  \u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d \u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d \n"  # noqa: E501
        "  \u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551\u2588\u2588\u2588\u2557\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2551  \u2588\u2588\u2588\u2588\u2588\u2557  \n"  # noqa: E501
        "  \u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2551\u255a\u2588\u2588\u2554\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2554\u2550\u2550\u255d  \n"  # noqa: E501
        "  \u2588\u2588\u2551     \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u255a\u2588\u2588\u2554\u2550\u2550\u2554\u2550\u2550\u2550\u255d\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \n"  # noqa: E501
        "  \u255a\u2550\u255d     \u255a\u2550\u2550\u2550\u2550\u2550\u255d  \u255a\u2550\u255d  \u255a\u255d     \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d [/]"  # noqa: E501
        "[bold white]GUARD[/]"
    )
    console.print()


def _print_choices(choices: dict, label: str) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", width=4)
    table.add_column()
    for k, (_, desc, _) in choices.items():
        table.add_row(f"[{k}]", desc)
    console.print(table)


def _print_notifier_choices() -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", width=4)
    table.add_column()
    rows = [
        ("1", "\U0001f4f1 Telegram bot (recommended \u2014 alerts on your phone)"),
        ("2", "\U0001f4ac Discord webhook (rich embeds)"),
        ("3", "\U0001f4ca Slack webhook (Block Kit)"),
        ("4", "\U0001f517 Custom webhook (HMAC-signed JSON)"),
        ("5", "\U0001f4e7 Email (SMTP)"),
        ("6", "\u2192 Done / continue"),
    ]
    for k, desc in rows:
        table.add_row(f"[{k}]", desc)
    console.print(table)


def _configure_notifier(ntype: str) -> tuple[dict | None, dict]:
    env: dict[str, str] = {}
    cfg: dict | None = {"type": ntype, "enabled": True}

    if ntype == "telegram":
        token = Prompt.ask("  Telegram Bot Token (from @BotFather)", password=True, default="")
        chat_id = Prompt.ask("  Telegram Chat ID", default="")
        if token:
            env["SERVERGUARD_TELEGRAM_BOT_TOKEN"] = token
        if chat_id:
            env["SERVERGUARD_TELEGRAM_CHAT_ID"] = chat_id
        console.print("  [dim]Get chat ID: message your bot, then call getUpdates API[/]")

    elif ntype == "discord":
        url = Prompt.ask("  Discord Webhook URL", password=True, default="")
        if url:
            env["SERVERGUARD_DISCORD_WEBHOOK_URL"] = url

    elif ntype == "slack":
        url = Prompt.ask("  Slack Webhook URL", password=True, default="")
        if url:
            env["SERVERGUARD_SLACK_WEBHOOK_URL"] = url

    elif ntype == "webhook":
        url = Prompt.ask("  Webhook URL", default="")
        secret = Prompt.ask("  Signing secret (optional, for HMAC verification)", default="")
        if url:
            env["SERVERGUARD_WEBHOOK_URL"] = url
        if secret:
            env["SERVERGUARD_WEBHOOK_SECRET"] = secret

    elif ntype == "email":
        host = Prompt.ask("  SMTP Host", default="smtp.gmail.com")
        port = Prompt.ask("  SMTP Port", default="587")
        user = Prompt.ask("  SMTP Username")
        pwd = Prompt.ask("  SMTP Password / App Password", password=True, default="")
        to = Prompt.ask("  Send alerts to (email address)")
        env.update(
            {
                "SERVERGUARD_SMTP_HOST": host,
                "SERVERGUARD_SMTP_PORT": port,
                "SERVERGUARD_SMTP_USER": user,
                "SERVERGUARD_SMTP_PASSWORD": pwd,
                "SERVERGUARD_SMTP_TO": to,
            }
        )

    return cfg, env


def _write_config(
    instance_id: str,
    provider_id: str,
    model: str,
    log_sources: list[dict],
    notifier_configs: list[dict],
) -> None:
    lines = [
        "[serverguard]",
        f'instance_id = "{instance_id}"',
        f'data_dir    = "{SG_HOME}/data"',
        "",
        "[security]",
        "max_lines_per_second = 10000",
        "",
        "[ai]",
        f'provider = "{provider_id}"',
    ]
    if model:
        lines.append(f'model    = "{model}"')
    lines += ["", ""]

    for ls in log_sources:
        lines += [
            "[[log_sources]]",
            f'name = "{ls["name"]}"',
            f'type = "{ls["type"]}"',
            f'path = "{ls["path"]}"',
            "",
        ]

    lines += [
        "[[detectors]]",
        'name                     = "ssh_bruteforce"',
        "enabled                  = true",
        f'source                   = "{log_sources[0]["name"] if log_sources else "auth"}"',
        "failed_attempt_threshold = 5",
        "window_seconds           = 60",
        "",
    ]

    for nc in notifier_configs:
        lines += [
            "[[notifiers]]",
            f'type    = "{nc["type"]}"',
            "enabled = true",
            "",
        ]

    DEFAULT_CONFIG.write_text("\n".join(lines))


def _write_env(api_key: str, env_var: str | None, extras: dict) -> None:
    lines = [
        "# ServerGuard secrets \u2014 DO NOT COMMIT THIS FILE",
        "# Generated by: sg setup",
        "",
    ]
    if env_var and api_key:
        lines.append(f"{env_var}={api_key}")
    for k, v in extras.items():
        lines.append(f"{k}={v}")
    DEFAULT_ENV.write_text("\n".join(lines))
    # Restrict permissions on the .env file (owner-read only)
    DEFAULT_ENV.chmod(0o600)
