"""Sampling logic to avoid processing every frame."""

from __future__ import annotations

import time


class FrameSampler:
    """Simple wall-clock based frame sampler."""

    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = max(0.1, float(interval_seconds))
        self._last_ts = 0.0

    def should_sample(self) -> bool:
        """Return True when enough time has elapsed since last sample."""
        now = time.time()
        if now - self._last_ts >= self.interval_seconds:
            self._last_ts = now
            return True
        return False
