import os
import threading
import time
from dataclasses import dataclass

FREE_REQUESTS = 3
DEFAULT_RATE_LIMIT_BASE_DELAY_SECONDS = 10.0
DEFAULT_RATE_LIMIT_RESET_SECONDS = 5 * 60

# multiplier per tier: 10s, 30s, 120s by default, then x4 per further tier
DELAY_MULTIPLIERS = [1, 3, 12]


def rate_limit_base_delay_seconds() -> float:
    """
    Length of the first escalation tier. Overridable via
    RATE_LIMIT_BASE_DELAY_SECONDS; 0 disables throttling entirely
    """
    raw = os.environ.get("RATE_LIMIT_BASE_DELAY_SECONDS")
    if raw:
        try:
            value = float(raw)
            if value >= 0:
                return value
        except ValueError:
            pass
    return DEFAULT_RATE_LIMIT_BASE_DELAY_SECONDS


def rate_limit_reset_seconds() -> float:
    """
    How long an ip must stay quiet before it gets a clean slate. Overridable
    via RATE_LIMIT_RESET_SECONDS so tests don't have to wait 5 minutes
    """
    raw = os.environ.get("RATE_LIMIT_RESET_SECONDS")
    if raw:
        try:
            value = float(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_RATE_LIMIT_RESET_SECONDS


def _required_delay_seconds(tier: int) -> float:
    if tier < len(DELAY_MULTIPLIERS):
        multiplier = DELAY_MULTIPLIERS[tier]
    else:
        multiplier = DELAY_MULTIPLIERS[-1] * 4 ** (tier - len(DELAY_MULTIPLIERS) + 1)
    return multiplier * rate_limit_base_delay_seconds()


@dataclass
class _Entry:
    allowed_count: int
    last_allowed_at: float


class RateLimiter:
    """
    Escalating per-ip backoff for POST /servers

    The first FREE_REQUESTS registrations go through immediately; each one
    after that waits progressively longer since the last allowed one. An ip
    quiet for rate_limit_reset_seconds() is swept and starts fresh
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, _Entry] = {}

    def check(self, ip: str) -> float | None:
        """Records the attempt; returns None if allowed, else seconds still to wait"""
        now = time.time()
        with self._lock:
            self._remove_stale_locked(now)
            entry = self._entries.get(ip)

            if entry is None or entry.allowed_count < FREE_REQUESTS:
                count = 0 if entry is None else entry.allowed_count
                self._entries[ip] = _Entry(allowed_count=count + 1, last_allowed_at=now)
                return None

            required = _required_delay_seconds(entry.allowed_count - FREE_REQUESTS)
            elapsed = now - entry.last_allowed_at
            if elapsed < required:
                return required - elapsed

            self._entries[ip] = _Entry(allowed_count=entry.allowed_count + 1, last_allowed_at=now)
            return None

    def _remove_stale_locked(self, now: float) -> None:
        reset = rate_limit_reset_seconds()
        stale = [ip for ip, entry in self._entries.items() if now - entry.last_allowed_at > reset]
        for ip in stale:
            del self._entries[ip]
