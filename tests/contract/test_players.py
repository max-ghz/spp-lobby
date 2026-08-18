from tests.contract.helpers import assert_error_response, register_and_require_created, valid_register_payload


def test_existing(client):
    payload = valid_register_payload(24001)
    payload["players"] = ["alice", "bob"]
    register_and_require_created(client, payload)

    resp = client.get("/servers/127.0.0.1/24001/players")

    assert resp.status_code == 200, resp.text
    assert "application/json" in resp.headers.get("content-type", "")
    assert resp.json() == ["alice", "bob"]


def test_not_found(client):
    resp = client.get("/servers/127.0.0.1/24099/players")
    assert_error_response(resp, 404, "server not found")


def test_empty_players_list(client):
    payload = valid_register_payload(24101)
    payload["players"] = []
    register_and_require_created(client, payload)

    resp = client.get("/servers/127.0.0.1/24101/players")

    assert resp.status_code == 200, resp.text
    assert resp.json() == []
    assert resp.text != "null"


def test_multiple_players(client):
    payload = valid_register_payload(24102)
    payload["max_players"] = 5
    payload["players"] = ["one", "two", "three", "four", "five"]
    register_and_require_created(client, payload)

    resp = client.get("/servers/127.0.0.1/24102/players")

    assert resp.json() == ["one", "two", "three", "four", "five"]


def test_invalid_port(client):
    resp = client.get("/servers/127.0.0.1/not-a-port/players")
    assert_error_response(resp, 400, "Invalid port")
