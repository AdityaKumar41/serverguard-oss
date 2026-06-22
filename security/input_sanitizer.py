"""Input sanitization — cleans all external data before processing.

All log lines, config values, and user-supplied strings pass through
this module before being used anywhere in the daemon or stored in SQLite.

Rules:
- Lines longer than MAX_LINE_BYTES are truncated and flagged.
- Null bytes and C0 control characters (except tab/newline) are stripped.
- Path traversal sequences are rejected in file paths.
- All output is guaranteed to be valid UTF-8.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum line length accepted from log files (4 KiB).
MAX_LINE_BYTES = 4096

# Characters allowed in log lines: printable ASCII + tab + newline.
# Control characters below 0x20 (except 0x09=tab, 0x0A=newline) are stripped.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

# Path traversal patterns to reject.
_TRAVERSAL_PATTERNS = ["..", "//", "\x00"]


def sanitize_log_line(line: str) -> str:
    """Sanitize one raw log line for safe processing.

    - Truncates lines exceeding MAX_LINE_BYTES
    - Strips dangerous control characters
    - Returns a clean UTF-8 string
    """
    # Encode/decode to ensure valid UTF-8 (replace broken sequences).
    line = line.encode("utf-8", errors="replace").decode("utf-8", errors="replace")

    # Truncate if too long.
    if len(line.encode("utf-8")) > MAX_LINE_BYTES:
        line = line.encode("utf-8")[:MAX_LINE_BYTES].decode("utf-8", errors="ignore")
        logger.debug("Log line truncated to %d bytes", MAX_LINE_BYTES)

    # Strip dangerous control characters.
    line = _CONTROL_RE.sub("", line)

    return line


def sanitize_string(value: str, max_length: int = 512) -> str:
    """Sanitize a general string value (config fields, subject, message).

    Safe for use in log output and SQLite storage.
    """
    if not isinstance(value, str):
        return ""
    value = value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    value = _CONTROL_RE.sub("", value)
    return value[:max_length]


def validate_file_path(path: str, must_exist: bool = True) -> Path:
    """Validate a file path from config. Raises ValueError on unsafe paths.

    Prevents path traversal, null bytes, and checks existence when required.
    """
    for pattern in _TRAVERSAL_PATTERNS:
        if pattern in path:
            raise ValueError(f"Unsafe path rejected (contains '{pattern}'): {path!r}")

    resolved = Path(path).resolve()

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"File not found: {path!r}")

    return resolved


def check_config_file_permissions(path: str) -> None:
    """Warn if the config file has overly permissive permissions.

    Config files may contain sensitive values. They should be readable
    only by the owner (mode 600 or 640).
    """
    try:
        mode = oct(os.stat(path).st_mode & 0o777)
        if os.stat(path).st_mode & 0o004:  # world-readable bit
            logger.warning(
                "Config file %s is world-readable (mode %s). Recommend: chmod 600 %s",
                path,
                mode,
                path,
            )
    except OSError:
        pass  # Existence check is handled elsewhere.


def check_data_dir_permissions(data_dir: str) -> None:
    """Warn if the data directory is world-writable."""
    try:
        p = Path(data_dir)
        if p.exists() and (os.stat(data_dir).st_mode & 0o002):
            logger.warning(
                "Data directory %s is world-writable. Recommend: chmod 750 %s",
                data_dir,
                data_dir,
            )
    except OSError:
        pass
