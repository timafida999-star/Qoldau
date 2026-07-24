"""Per-message limits for the chat socket.
"""
import time
from collections import deque
from typing import Deque, Dict, Hashable

MAX_MESSAGE_CHARS = 2000

MAX_MESSAGES_PER_WINDOW = 20
RATE_WINDOW_SECONDS = 10.0

_SWEEP_EVERY = 256


class SlidingWindowLimiter:
    """Allows at most ``max_events`` per ``window_seconds`` for each key."""

    def __init__(
        self, max_events: int, window_seconds: float, sweep_every: int = _SWEEP_EVERY
    ) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self.sweep_every = sweep_every
        self._events: Dict[Hashable, Deque[float]] = {}
        self._calls_since_sweep = 0

    def allow(self, key: Hashable) -> bool:
        now = time.monotonic()
        self._maybe_sweep(now)

        events = self._events.setdefault(key, deque())
        while events and now - events[0] >= self.window_seconds:
            events.popleft()

        if len(events) >= self.max_events:
            return False

        events.append(now)
        return True

    def _maybe_sweep(self, now: float) -> None:
        """Drop keys whose events have all aged out, so idle users don't leak."""
        self._calls_since_sweep += 1
        if self._calls_since_sweep < self.sweep_every:
            return
        self._calls_since_sweep = 0
        stale = [
            key
            for key, events in self._events.items()
            if not events or now - events[-1] >= self.window_seconds
        ]
        for key in stale:
            del self._events[key]

    def reset(self) -> None:
        self._events.clear()
        self._calls_since_sweep = 0


message_limiter = SlidingWindowLimiter(MAX_MESSAGES_PER_WINDOW, RATE_WINDOW_SECONDS)
