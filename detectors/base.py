"""Detector base class — all detectors implement this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from events.model import Event
from parsers.ssh_auth import FailedSSHAttempt


class Detector(ABC):
    """Abstract base for all ServerGuard detectors."""

    @abstractmethod
    def feed(self, attempt: FailedSSHAttempt) -> Iterator[Event]:
        """Feed one parsed attempt into the detector.

        Yields zero or more Events. Implementations must be stateful —
        they accumulate attempts internally and emit an event only when
        the detection rule triggers.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state (used between test runs)."""
        ...
