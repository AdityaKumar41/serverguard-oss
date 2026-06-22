"""Pytest configuration — sets asyncio mode for async tests."""

import pytest


# This makes all async test functions in the suite use pytest-asyncio automatically.
# Equivalent to setting asyncio_mode = "auto" in pyproject.toml (which we already have).
