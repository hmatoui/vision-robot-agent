"""Unit tests for temporal scene memory."""

from __future__ import annotations

import time

from app.memory.temporal_store import TemporalStore


def test_temporal_store_add_and_context() -> None:
    store = TemporalStore(retention_seconds=60, max_entries=3)
    store.add("person near desk")
    store.add("person walking")

    context = store.to_prompt_context()
    assert "person near desk" in context
    assert "person walking" in context


def test_temporal_store_max_entries() -> None:
    store = TemporalStore(retention_seconds=60, max_entries=2)
    store.add("a")
    store.add("b")
    store.add("c")

    entries = store.list()
    assert len(entries) == 2
    assert entries[0].description == "b"
    assert entries[1].description == "c"


def test_temporal_store_retention() -> None:
    store = TemporalStore(retention_seconds=1, max_entries=10)
    store.add("old")
    time.sleep(1.1)
    store.add("new")

    entries = store.list()
    assert len(entries) == 1
    assert entries[0].description == "new"
