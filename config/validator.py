"""Config validation rules — implements all v1 spec constraints."""

from __future__ import annotations

# Supported log source types in v1.
SUPPORTED_SOURCE_TYPES = {"ssh_auth"}

# Supported detector names in v1.
SUPPORTED_DETECTOR_NAMES = {"ssh_bruteforce"}


def validate(config) -> None:  # type: ignore[no-untyped-def]
    """Validate a parsed Config object against all v1 rules.

    Raises:
        ValueError: with a clear message on the first failed rule.
    """
    _validate_serverguard_section(config.serverguard)
    _validate_log_sources(config.log_sources)
    _validate_detectors(config.detectors, config.log_sources)


def _validate_serverguard_section(sg) -> None:  # type: ignore[no-untyped-def]
    if not sg.instance_id:
        raise ValueError("serverguard.instance_id must be non-empty")
    if not sg.data_dir:
        raise ValueError("serverguard.data_dir must be non-empty")


def _validate_log_sources(log_sources) -> None:  # type: ignore[no-untyped-def]
    seen_names: set[str] = set()
    for ls in log_sources:
        if not ls.name:
            raise ValueError("log_sources: each entry must have a non-empty name")
        if ls.name in seen_names:
            raise ValueError(f"log_sources: duplicate name '{ls.name}'")
        seen_names.add(ls.name)
        if not ls.path:
            raise ValueError(f"log_sources[{ls.name}]: path must be non-empty")
        if ls.type not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(
                f"log_sources[{ls.name}]: unsupported type '{ls.type}' "
                f"(supported: {sorted(SUPPORTED_SOURCE_TYPES)})"
            )


def _validate_detectors(detectors, log_sources) -> None:  # type: ignore[no-untyped-def]
    source_names = {ls.name for ls in log_sources}
    seen_names: set[str] = set()
    for d in detectors:
        if not d.name:
            raise ValueError("detectors: each entry must have a non-empty name")
        if d.name in seen_names:
            raise ValueError(f"detectors: duplicate name '{d.name}'")
        seen_names.add(d.name)
        if d.enabled and d.source not in source_names:
            raise ValueError(
                f"detectors[{d.name}]: references unknown log source '{d.source}'"
            )
        if d.failed_attempt_threshold <= 0:
            raise ValueError(
                f"detectors[{d.name}]: failed_attempt_threshold must be > 0"
            )
        if d.window_seconds <= 0:
            raise ValueError(f"detectors[{d.name}]: window_seconds must be > 0")
