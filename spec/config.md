# ServerGuard Configuration Specification

## Purpose

This document defines the v1 configuration format shared by the Go, Rust, and C++ implementations.

The format is language-neutral. Implementations may use different parsing libraries, but they must accept the same fields, apply the same validation rules, and produce equivalent errors.

## Format

The v1 configuration format is TOML.

Example:

```toml
[serverguard]
instance_id = "local-dev"
data_dir = "./data"

[[log_sources]]
name = "auth"
path = "./fixtures/logs/auth.log"
type = "ssh_auth"

[[detectors]]
name = "ssh_bruteforce"
enabled = true
source = "auth"
failed_attempt_threshold = 5
window_seconds = 60
```

## Top-Level Sections

Required sections:

- `[serverguard]`
- `[[log_sources]]`
- `[[detectors]]`

## ServerGuard Section

Required fields:

- `instance_id`
- `data_dir`

Validation rules:

- `instance_id` must be non-empty
- `data_dir` must be non-empty

## Log Sources

Each `[[log_sources]]` entry describes one input file.

Required fields:

- `name`
- `path`
- `type`

Validation rules:

- `name` must be non-empty
- `name` must be unique
- `path` must be non-empty
- `type` must be supported

Supported types in v1:

- `ssh_auth`

## Detectors

Each `[[detectors]]` entry describes one enabled or disabled detector instance.

Required fields:

- `name`
- `enabled`
- `source`
- `failed_attempt_threshold`
- `window_seconds`

Validation rules:

- `name` must be non-empty
- `name` must be unique
- `source` must reference an existing `log_sources.name`
- `failed_attempt_threshold` must be greater than zero
- `window_seconds` must be greater than zero

Supported detector names in v1:

- `ssh_bruteforce`

## Path Rules

Implementations must support relative paths in the config file.

For v1, relative paths should be resolved relative to the working directory used to launch the process unless the implementation later adopts a stricter shared rule. That rule must remain identical across all three implementations.

## Error Expectations

Implementations must return clear errors for:

- missing config file
- invalid TOML syntax
- missing required section
- missing required field
- duplicate source name
- duplicate detector name
- unsupported source type
- detector referencing an unknown source
- invalid numeric values

The exact wording may differ, but the failure reason must be obvious.
