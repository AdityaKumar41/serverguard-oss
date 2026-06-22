"""Unit tests for SSH auth log parser."""

from __future__ import annotations

from parsers.ssh_auth import parse_line

# ── Matching lines ────────────────────────────────────────────────────────────


def test_parse_invalid_user_line() -> None:
    line = (
        "Apr 25 10:15:01 host sshd[1234]: Failed password for invalid user admin "
        "from 203.0.113.10 port 54321 ssh2"
    )
    result = parse_line(line)
    assert result is not None
    assert result.ip == "203.0.113.10"
    assert result.username == "admin"
    assert result.port == 54321
    assert result.timestamp_text == "Apr 25 10:15:01"


def test_parse_valid_user_line() -> None:
    line = (
        "Apr 25 10:15:03 host sshd[1235]: Failed password for root "
        "from 203.0.113.10 port 54322 ssh2"
    )
    result = parse_line(line)
    assert result is not None
    assert result.ip == "203.0.113.10"
    assert result.username == "root"
    assert result.port == 54322


def test_raw_line_preserved() -> None:
    line = (
        "Apr 25 10:15:01 host sshd[1234]: Failed password for invalid user admin "
        "from 1.2.3.4 port 1000 ssh2"
    )
    result = parse_line(line)
    assert result is not None
    assert result.raw_line == line.strip()


# ── Non-matching lines must return None ───────────────────────────────────────


def test_accepted_publickey_line_returns_none() -> None:
    line = (
        "Apr 25 10:16:05 host sshd[1240]: Accepted publickey for deploy "
        "from 198.51.100.20 port 60211 ssh2"
    )
    assert parse_line(line) is None


def test_cron_line_returns_none() -> None:
    line = (
        "Apr 25 10:16:20 host CRON[1241]: pam_unix(cron:session): session opened "
        "for user root(uid=0) by root(uid=0)"
    )
    assert parse_line(line) is None


def test_empty_line_returns_none() -> None:
    assert parse_line("") is None


def test_garbage_line_returns_none() -> None:
    assert parse_line("!!!not a log line!!!") is None


# ── Robustness: must never raise ──────────────────────────────────────────────


def test_none_like_content_does_not_raise() -> None:
    # parse_line must tolerate any string without raising.
    parse_line("None")
    parse_line("\x00\x01\x02")
    parse_line("a" * 10000)
