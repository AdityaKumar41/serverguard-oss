"""Configuration data models for ServerGuard."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ServerGuardSection:
    """Top-level [serverguard] config block."""

    instance_id: str
    data_dir: str


@dataclass
class LogSource:
    """A [[log_sources]] entry — one watched file."""

    name: str
    path: str
    type: str  # e.g. "ssh_auth"


@dataclass
class DetectorConfig:
    """A [[detectors]] entry — one detection rule instance."""

    name: str
    enabled: bool
    source: str
    failed_attempt_threshold: int
    window_seconds: int


@dataclass
class Config:
    """Complete parsed and validated ServerGuard configuration."""

    serverguard: ServerGuardSection
    log_sources: list[LogSource] = field(default_factory=list)
    detectors: list[DetectorConfig] = field(default_factory=list)
    config_path: str = ""  # absolute path of the loaded config file

    @property
    def db_path(self) -> str:
        import os

        return os.path.join(self.serverguard.data_dir, "serverguard.db")

    @property
    def audit_db_path(self) -> str:
        import os

        return os.path.join(self.serverguard.data_dir, "audit.db")
