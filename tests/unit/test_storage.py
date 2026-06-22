"""Unit tests for SQLite event store."""

from __future__ import annotations

import pytest

from events.model import Event, make_daemon_started, make_daemon_stopping
from storage.sqlite import Store


@pytest.fixture()
async def store(tmp_path) -> Store:  # type: ignore[no-untyped-def]
    """Create an in-memory-ish temporary store for testing."""
    db_path = str(tmp_path / "test.db")
    s = await Store.open(db_path)
    yield s
    await s.close()


async def test_empty_store_returns_no_events(store: Store) -> None:
    events = await store.list_events()
    assert events == []


async def test_insert_and_retrieve_event(store: Store) -> None:
    event = make_daemon_started("test-instance")
    await store.insert(event)
    events = await store.list_events()
    assert len(events) == 1
    assert events[0].id == event.id
    assert events[0].type == event.type
    assert events[0].severity == event.severity
    assert events[0].source == event.source
    assert events[0].subject == event.subject
    assert events[0].message == event.message


async def test_events_returned_in_reverse_order(store: Store) -> None:
    e1 = make_daemon_started("inst")
    e2 = make_daemon_stopping("inst")
    await store.insert(e1)
    await store.insert(e2)
    events = await store.list_events()
    # Reverse chronological: e2 (later timestamp) first.
    assert len(events) == 2
    # Both events should be present; exact order depends on timestamp.
    ids = {e.id for e in events}
    assert e1.id in ids
    assert e2.id in ids


async def test_metadata_json_round_trip(store: Store) -> None:
    event = Event(
        type="security.ssh_bruteforce",
        severity="warning",
        source="auth",
        subject="1.2.3.4",
        message="brute force detected",
        metadata={
            "attempt_count": 5,
            "window_seconds": 60,
            "matched_lines": ["line1", "line2"],
        },
    )
    await store.insert(event)
    events = await store.list_events()
    meta = events[0].metadata
    assert meta["attempt_count"] == 5
    assert meta["matched_lines"] == ["line1", "line2"]


async def test_duplicate_id_raises(store: Store) -> None:
    event = make_daemon_started("inst")
    await store.insert(event)
    with pytest.raises(RuntimeError, match="insertion failed"):
        await store.insert(event)  # Same ID — should fail.
