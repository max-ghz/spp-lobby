import time

from tests.contract.helpers import SERVER_FIELDS, register_and_require_created, valid_register_payload


def test_empty_list(client):
    resp = client.get("/servers")

    assert resp.status_code == 200, resp.text
    assert "application/json" in resp.headers.get("content-type", "")
    assert resp.json() == []
    assert resp.text != "null"


def test_one_server(client):
    register_and_require_created(client, valid_register_payload(22001))

    servers = client.get("/servers").json()

    assert len(servers) == 1, servers
    assert servers[0]["port"] == 22001
    assert servers[0]["ip"] == "127.0.0.1"


def test_multiple_servers(client):
    ports = [22101, 22102, 22103]
    for port in ports:
        payload = valid_register_payload(port)
        payload["name"] = f"server-{port}"
        register_and_require_created(client, payload)

    servers = client.get("/servers").json()

    assert len(servers) == len(ports), servers
    seen = {s["port"] for s in servers}
    for port in ports:
        assert port in seen, f"port {port} missing from the list"


def test_reflects_updated_server(client):
    register_and_require_created(client, valid_register_payload(22201))

    updated = valid_register_payload(22201)
    updated["name"] = "Updated Name"
    register_and_require_created(client, updated)

    servers = client.get("/servers").json()

    assert len(servers) == 1, servers
    assert servers[0]["name"] == "Updated Name"


def test_expired_server_is_removed(client, monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "1")
    register_and_require_created(client, valid_register_payload(22301))

    time.sleep(2.2)

    servers = client.get("/servers").json()
    for s in servers:
        assert s["port"] != 22301, f"expired server (port 22301) still present: {s}"


def test_response_is_a_json_array(client):
    register_and_require_created(client, valid_register_payload(22401))

    raw = client.get("/servers").json()

    assert len(raw) == 1
    for key in SERVER_FIELDS:
        assert key in raw[0], f"list entry missing field {key!r}"
