"""Temporal observation storage for short-term scene memory."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, List


@dataclass(slots=True)
class Observation:
    """A timestamped scene observation."""

    timestamp: datetime
    description: str


class TemporalStore:
    """Time-windowed ring buffer for scene observations."""

    def __init__(self, retention_seconds: int = 60, max_entries: int = 12) -> None:
        self.retention_seconds = retention_seconds
        self.max_entries = max_entries
        self._items: Deque[Observation] = deque(maxlen=max_entries)

    def add(self, description: str) -> Observation:
        """Append an observation and evict stale entries."""
        obs = Observation(timestamp=datetime.utcnow(), description=description.strip())
        self._items.append(obs)
        self.prune()
        return obs

    def prune(self) -> None:
        """Remove entries older than retention window."""
        threshold = datetime.utcnow() - timedelta(seconds=self.retention_seconds)
        while self._items and self._items[0].timestamp < threshold:
            self._items.popleft()

    def list(self) -> List[Observation]:
        """Return current observations in chronological order."""
        self.prune()
        return list(self._items)

    def to_prompt_context(self) -> str:
        """Format recent observations for LLM prompt context."""
        entries = self.list()
        if not entries:
            return "No recent observations."
        return "\n".join(
            f"{item.timestamp.strftime('%H:%M:%S')} — {item.description}" for item in entries
        )
