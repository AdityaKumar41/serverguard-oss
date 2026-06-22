"""Rate limiter — prevents log flooding attacks from exhausting CPU/memory.

A log flooding attack writes millions of lines to a watched log file to:
- Exhaust CPU in regex parsing
- Fill RAM with detection history
- Overwhelm the event database

The rate limiter enforces a maximum line ingestion rate per source.
Lines exceeding the rate are dropped and counted. A warning event is
emitted when the rate is first exceeded, and again when it subsides.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Default max lines per second per source before rate limiting kicks in.
DEFAULT_MAX_LINES_PER_SECOND = 10_000


@dataclass
class RateLimiter:
    """Token-bucket rate limiter for log line ingestion.

    Thread-safe for single-producer async use (no locks needed since
    asyncio is cooperative and we run within one event loop).
    """

    source_name: str
    max_per_second: int = DEFAULT_MAX_LINES_PER_SECOND

    # Sliding window: timestamps of recent line arrivals (deque for O(1) pop).
    _window: deque[float] = field(default_factory=deque, init=False, repr=False)
    _dropped: int = field(default=0, init=False, repr=False)
    _limiting: bool = field(default=False, init=False, repr=False)

    def allow(self) -> bool:
        """Return True if the next line should be processed.

        Maintains a 1-second sliding window. If the count of lines
        in the last second exceeds max_per_second, returns False.
        """
        now = time.monotonic()
        cutoff = now - 1.0

        # Evict timestamps older than 1 second.
        while self._window and self._window[0] < cutoff:
            self._window.popleft()

        if len(self._window) >= self.max_per_second:
            self._dropped += 1
            if not self._limiting:
                self._limiting = True
                logger.warning(
                    "[%s] Rate limit exceeded (%d lines/sec). "
                    "Dropping excess lines to protect system resources.",
                    self.source_name,
                    self.max_per_second,
                )
            return False

        # Rate is within limit.
        self._window.append(now)
        if self._limiting and len(self._window) < self.max_per_second // 2:
            logger.info(
                "[%s] Rate limit subsided. %d lines were dropped.",
                self.source_name,
                self._dropped,
            )
            self._limiting = False
            self._dropped = 0

        return True

    @property
    def dropped_count(self) -> int:
        """Total lines dropped since last reset."""
        return self._dropped
