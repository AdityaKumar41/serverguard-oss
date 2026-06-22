"""Log file watcher — polls a file for new lines at a configurable interval.

For v1, polling is used instead of platform-specific file notification APIs
(inotify, kqueue) to keep behavior identical across Linux and macOS.

The watcher tracks the byte offset of the last read position so it never
re-delivers already-processed lines during one daemon run.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Callable, Awaitable

logger = logging.getLogger(__name__)

# Default polling interval in seconds.
POLL_INTERVAL = 1.0


class LogWatcher:
    """Tail a log file and yield new lines as they appear.

    Usage:
        watcher = LogWatcher("/var/log/auth.log")
        async for line in watcher.watch():
            process(line)
    """

    def __init__(
        self, path: str, poll_interval: float = POLL_INTERVAL, replay: bool = False
    ) -> None:
        self._path = Path(path)
        self._poll_interval = poll_interval
        self._offset: int = 0
        self._running = False

        if not replay and self._path.exists():
            # Production mode: start from end of file to only tail new lines.
            self._offset = self._path.stat().st_size
        # replay=True: start from offset 0, processing all existing content.

    async def watch(self) -> AsyncIterator[str]:
        """Yield new lines from the file indefinitely until stop() is called."""
        if not self._path.exists():
            raise FileNotFoundError(f"Log file not found: {self._path}")

        self._running = True
        while self._running:
            try:
                with self._path.open("r", encoding="utf-8", errors="replace") as f:
                    f.seek(self._offset)
                    for line in f:
                        yield line
                    self._offset = f.tell()
            except OSError as exc:
                logger.warning("Log watcher read error (%s): %s", self._path, exc)

            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        """Signal the watcher to stop after the current poll."""
        self._running = False
