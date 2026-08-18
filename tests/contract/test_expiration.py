import time

from tests.contract.helpers import assert_error_response, register_and_require_created, valid_register_payload


def test_registration(client, monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "2")
    register_and_require_created(client, valid_register_payload(25001))

    resp = client.get("/servers/127.0.0.1/25001")
    assert resp.status_code == 200, resp.text


def test_update_resets_the_timer(client, monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "2")
    register_and_require_created(client, valid_register_payload(25101))

    # heartbeat shortly before the original registration would expire
    time.sleep(1.2)
    register_and_require_created(client, valid_register_payload(25101))

    # past the original TTL, but under 2s since the heartbeat above
    time.sleep(1.2)

    resp = client.get("/servers/127.0.0.1/25101")
    assert resp.status_code == 200, resp.text


def test_expiration(client, monkeypatch):
    monkeypatch.setenv("SERVER_EXPIRY_TIME_IN_SECONDS", "1")
    register_and_require_created(client, valid_register_payload(25201))

    time.sleep(2.2)

    specific = client.get("/servers/127.0.0.1/25201")
    assert_error_response(specific, 404, "server not found")

    players = client.get("/servers/127.0.0.1/25201/players")
    assert_error_response(players, 404, "server not found")

    servers = client.get("/servers").json()
    for s in servers:
        assert s["port"] != 25201, f"expired server still present in GET /servers: {s}"
