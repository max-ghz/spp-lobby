import threading

from tests.contract.helpers import valid_register_payload


def test_get_servers_during_concurrent_post(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "0")  # would otherwise throttle these rapid posts
    writers = 10  # the per-ip registration limit, since every writer shares the client's ip
    readers = 25
    problems: list[str] = []
    lock = threading.Lock()

    def write(i: int) -> None:
        payload = valid_register_payload(24000 + i)
        resp = client.post("/servers", json=payload)
        if resp.status_code != 201:
            with lock:
                problems.append(f"writer {i}: POST returned {resp.status_code}")

    def read(i: int) -> None:
        for _ in range(10):
            resp = client.get("/servers")
            if resp.status_code != 200:
                with lock:
                    problems.append(f"reader {i}: GET returned {resp.status_code}")

    threads = [threading.Thread(target=write, args=(i,)) for i in range(writers)]
    threads += [threading.Thread(target=read, args=(i,)) for i in range(readers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not problems, problems

    servers = client.get("/servers").json()
    assert len(servers) == writers, f"expected {writers} servers, got {len(servers)}"


def test_get_specific_server_during_update(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "0")  # would otherwise throttle these rapid posts
    ip = "127.0.0.1"
    port = 24100
    client.post("/servers", json=valid_register_payload(port))

    problems: list[str] = []
    lock = threading.Lock()

    def update(i: int) -> None:
        for j in range(20):
            payload = valid_register_payload(port)
            payload["name"] = f"update-{i}-{j}"
            resp = client.post("/servers", json=payload)
            if resp.status_code != 201:
                with lock:
                    problems.append(f"updater {i}/{j}: POST returned {resp.status_code}")

    def read(i: int) -> None:
        for j in range(20):
            resp = client.get(f"/servers/{ip}/{port}")
            if resp.status_code != 200:
                with lock:
                    problems.append(f"reader {i}/{j}: GET returned {resp.status_code}")

    threads = [threading.Thread(target=update, args=(i,)) for i in range(8)]
    threads += [threading.Thread(target=read, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not problems, problems

    servers = client.get("/servers").json()
    matching = [s for s in servers if s["ip"] == ip and s["port"] == port]
    assert len(matching) == 1, f"expected exactly 1 entry, found {len(matching)}"
