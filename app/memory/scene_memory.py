"""High-level scene memory wrapper around temporal store."""

from __future__ import annotations

from typing import Any

from app.memory.temporal_store import TemporalStore


class SceneMemory:
    """Encapsulates scene memory operations and serialization."""

    def __init__(self, retention_seconds: int = 60, max_entries: int = 12) -> None:
        self._store = TemporalStore(
            retention_seconds=retention_seconds, max_entries=max_entries
        )

    def add_observation(self, description: str) -> None:
        """Add new memory observation."""
        self._store.add(description)

    def get_context(self) -> str:
        """Get memory formatted for prompting."""
        return self._store.to_prompt_context()

    def get_observations(self) -> list[dict[str, Any]]:
        """Get memory as API-friendly dictionaries."""
        return [
            {
                "timestamp": obs.timestamp.isoformat(),
                "description": obs.description,
            }
            for obs in self._store.list()
        ]
