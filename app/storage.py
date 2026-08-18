import os
import threading
import time
from dataclasses import dataclass

from app.models import RegisterServerInput, Server

DEFAULT_SERVER_EXPIRY_SECONDS = 5 * 60


def server_expiry_seconds() -> int:
    """
    TTL after which a server is dropped. Overridable via
    SERVER_EXPIRY_TIME_IN_SECONDS so tests don't have to wait 5 minutes
    """
    raw = os.environ.get("SERVER_EXPIRY_TIME_IN_SECONDS")
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_SERVER_EXPIRY_SECONDS


@dataclass
class _Entry:
    server: Server
    updated_at: int


class ServerStore:
    """
    In-memory, thread-safe server registry

    A single dict keyed by (ip, port), guarded by one lock for every
    operation. Re-registering a key deletes it before re-inserting, so
    iteration order stays oldest-updated first
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._servers: dict[tuple[str, int], _Entry] = {}

    def register(self, ip: str, input: RegisterServerInput) -> None:
        server = Server.from_input(input, ip)
        key = (ip, input.port)
        with self._lock:
            self._servers.pop(key, None)
            self._servers[key] = _Entry(server=server, updated_at=int(time.time()))

    def get(self, ip: str, port: int) -> Server | None:
        with self._lock:
            self._remove_expired_locked()
            entry = self._servers.get((ip, port))
            return entry.server if entry else None

    def list(self) -> list[Server]:
        with self._lock:
            self._remove_expired_locked()
            return [entry.server for entry in self._servers.values()]

    def _remove_expired_locked(self) -> None:
        now = int(time.time())
        ttl = server_expiry_seconds()
        expired = [key for key, entry in self._servers.items() if now - entry.updated_at > ttl]
        for key in expired:
            del self._servers[key]
