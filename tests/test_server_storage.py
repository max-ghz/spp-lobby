import threading
import time

from features.servers.models import RegisterServerInput
from features.servers.services.server_storage import (
    DEFAULT_SERVER_EXPIRY_SECONDS,
    ServerStorage,
    server_expiry_seconds,
)


def _input(port: int, **overrides) -> RegisterServerInput:
    kwargs = {
        "advanced": False,
        "anti_cheat_on": False,
        "bonus_frequency": 0,
        "country": "PL",
        "current_map": "ctf_Ash",
        "game_style": "CTF",
        "info": "",
        "max_players": 16,
        "name": "Test",
        "num_bots": 0,
        "os": "Linux",
        "players": [],
        "port": port,
        "private": False,
        "realistic": False,
        "respawn": 0,
        "survival": False,
        "version": "1.0",
        "wm": False,
    }
    kwargs.update(overrides)
    return RegisterServerInput(**kwargs)


def test_server_expiry_seconds_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("SERVER_EXPIRY_TIME_IN_SECONDS", raising=False)
    assert server_expiry_seconds() == DEFAULT_SERVER_EXPIRY_SECONDS


def test_server_expiry_seconds_falls_back_on_garbage_value(monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "not-a-number")
    assert server_expiry_seconds() == DEFAULT_SERVER_EXPIRY_SECONDS


def test_server_expiry_seconds_falls_back_on_non_positive_value(monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "0")
    assert server_expiry_seconds() == DEFAULT_SERVER_EXPIRY_SECONDS

    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "-5")
    assert server_expiry_seconds() == DEFAULT_SERVER_EXPIRY_SECONDS


def test_server_expiry_seconds_honors_valid_override(monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "42")
    assert server_expiry_seconds() == 42


def test_get_not_found():
    store = ServerStorage()
    assert store.get("10.0.0.1", 12345) is None


def test_get_found():
    store = ServerStorage()
    store.register("10.0.0.1", _input(12345))

    server = store.get("10.0.0.1", 12345)

    assert server is not None
    assert server.ip == "10.0.0.1"
    assert server.port == 12345


def test_empty_store_list_is_empty():
    store = ServerStorage()
    assert store.list() == []


def test_removes_only_expired_entries(monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", str(DEFAULT_SERVER_EXPIRY_SECONDS))
    store = ServerStorage()
    now = int(time.time())

    store.register("1.1.1.1", _input(1000))
    store.register("2.2.2.2", _input(2000))
    store.register("3.3.3.3", _input(3000))

    # Backdate directly, bypassing register()'s real-time stamping, that's the
    # only way to simulate "already old" without sleeping for real
    store._servers[("2.2.2.2", 2000)].updated_at = now - DEFAULT_SERVER_EXPIRY_SECONDS + 2
    store._servers[("3.3.3.3", 3000)].updated_at = now - DEFAULT_SERVER_EXPIRY_SECONDS - 5

    servers = store.list()

    ips = {s.ip for s in servers}
    assert "1.1.1.1" in ips, "a freshly-registered server must survive a sweep"
    assert "2.2.2.2" in ips, "a server just under the TTL boundary must survive a sweep"
    assert "3.3.3.3" not in ips, "a server past the TTL must be removed"


def test_exact_ttl_boundary(monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "100")
    store = ServerStorage()
    now = int(time.time())

    store.register("4.4.4.4", _input(4000))
    store.register("5.5.5.5", _input(5000))
    store._servers[("4.4.4.4", 4000)].updated_at = now - 100
    store._servers[("5.5.5.5", 5000)].updated_at = now - 101

    servers = store.list()
    ips = {s.ip for s in servers}

    assert "4.4.4.4" in ips, "a server exactly at the TTL boundary must not be expired yet"
    assert "5.5.5.5" not in ips, "a server one second past the TTL boundary must be expired"


def test_updating_a_server_moves_it_to_the_end_of_the_list():
    # GET /servers is ordered oldest-updated first, so re-registering an
    # entry must move it past anything that hasn't been touched since
    store = ServerStorage()
    store.register("1.1.1.1", _input(1000))
    store.register("2.2.2.2", _input(2000))

    store.register("1.1.1.1", _input(1000))  # re-register the first one

    ips_in_order = [s.ip for s in store.list()]
    assert ips_in_order == ["2.2.2.2", "1.1.1.1"]


def test_update_overwrites_and_deduplicates():
    store = ServerStorage()
    store.register("9.9.9.9", _input(23073, name="Old Name"))
    store.register("9.9.9.9", _input(23073, name="New Name"))

    servers = store.list()

    assert len(servers) == 1
    assert servers[0].name == "New Name"


def test_concurrent_registration_of_different_servers_loses_nothing():
    store = ServerStorage()
    n = 50

    def register(i: int) -> None:
        store.register("6.6.6.6", _input(30000 + i, name=f"server-{i}"))

    threads = [threading.Thread(target=register, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(store.list()) == n


def test_concurrent_reregistration_of_the_same_server_never_duplicates():
    store = ServerStorage()
    n = 50

    def register(i: int) -> None:
        store.register("7.7.7.7", _input(23073, name=f"server-{i}"))

    threads = [threading.Thread(target=register, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    servers = store.list()
    matching = [s for s in servers if s.ip == "7.7.7.7" and s.port == 23073]
    assert len(matching) == 1, f"expected exactly 1 entry, found {len(matching)}"


def test_concurrent_registration_and_expiry_sweeps_are_consistent(monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "100")
    store = ServerStorage()
    now = int(time.time())

    for i in range(10):
        store.register("8.8.8.8", _input(40000 + i))
        store._servers[("8.8.8.8", 40000 + i)].updated_at = now - 200  # already expired

    def register_fresh(i: int) -> None:
        store.register("9.9.9.9", _input(41000 + i))

    def sweep() -> None:
        for _ in range(20):
            store.list()

    threads = [threading.Thread(target=register_fresh, args=(i,)) for i in range(10)]
    threads += [threading.Thread(target=sweep) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    servers = store.list()
    assert all(s.ip != "8.8.8.8" for s in servers), "pre-expired servers must be gone"
    assert sum(1 for s in servers if s.ip == "9.9.9.9") == 10, "all fresh registrations must survive"
