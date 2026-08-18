import json

import pytest

from tests.contract.helpers import (
    REQUIRED_FIELDS,
    SERVER_FIELDS,
    assert_error_response,
    register_and_require_created,
    valid_register_payload,
)


def test_valid_request(client):
    resp = client.post("/servers", json=valid_register_payload(20001))

    assert resp.status_code == 201, resp.text
    assert "application/json" in resp.headers.get("content-type", "")
    assert resp.json() == {}


def test_content_type_header_is_ignored_for_parsing(client):
    body = valid_register_payload(20002)
    resp = client.post("/servers", content=json.dumps(body), headers={"content-type": "text/plain"})

    assert resp.status_code == 201, resp.text


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_missing_required_field(client, field):
    payload = valid_register_payload(20100)
    del payload[field]

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_null_required_field(client, field):
    payload = valid_register_payload(20200)
    payload[field] = None

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_empty_optional_strings_are_accepted(client):
    payload = valid_register_payload(20300)
    payload["country"] = ""
    payload["info"] = ""

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text


def test_empty_players_list_is_accepted(client):
    payload = valid_register_payload(20301)
    payload["players"] = []

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text


@pytest.mark.parametrize("field", ["current_map", "game_style", "name", "os", "version"])
def test_empty_required_strings_are_rejected(client, field):
    payload = valid_register_payload(20400)
    payload[field] = ""

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


@pytest.mark.parametrize(
    ("field", "max_len"),
    [
        ("country", 2),
        ("current_map", 16),
        ("game_style", 3),
        ("info", 255),
        ("name", 30),
        ("os", 10),
        ("version", 10),
    ],
)
def test_too_long_strings(client, field, max_len):
    payload = valid_register_payload(20500)
    payload[field] = "a" * (max_len + 1)

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_strings_exactly_at_max_length_are_accepted(client):
    payload = valid_register_payload(20600)
    payload["country"] = "a" * 2
    payload["current_map"] = "a" * 16
    payload["game_style"] = "a" * 3
    payload["info"] = "a" * 255
    payload["name"] = "a" * 30
    payload["os"] = "a" * 10
    payload["version"] = "a" * 10
    payload["players"] = ["a" * 16]
    payload["max_players"] = 1

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text


def test_too_long_player_name(client):
    payload = valid_register_payload(20601)
    payload["players"] = ["a" * 17]
    payload["max_players"] = 5

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_too_many_players(client):
    payload = valid_register_payload(20700)
    payload["max_players"] = 2
    payload["players"] = ["a", "b", "c"]

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_players_equal_to_max_players_is_accepted(client):
    payload = valid_register_payload(20701)
    payload["max_players"] = 2
    payload["players"] = ["a", "b"]

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text


def test_max_players_zero(client):
    payload = valid_register_payload(20800)
    payload["max_players"] = 0
    payload["players"] = []

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_port_zero(client):
    payload = valid_register_payload(0)

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_port_max_65535(client):
    payload = valid_register_payload(65535)
    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text

    get = client.get("/servers/127.0.0.1/65535")
    assert get.status_code == 200, get.text
    assert get.json()["port"] == 65535


def test_port_out_of_range(client):
    payload = valid_register_payload(0)
    payload["port"] = 65536

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 400, resp.text
    assert "application/json" in resp.headers.get("content-type", "")


def test_minimal_valid_values(client):
    payload = {
        "advanced": False, "anti_cheat_on": False, "bonus_frequency": 0,
        "country": "", "current_map": "a", "game_style": "a", "info": "",
        "max_players": 1, "name": "a", "num_bots": 0, "os": "a",
        "players": [], "port": 1, "private": False, "realistic": False,
        "respawn": 0, "survival": False, "version": "a", "wm": False,
    }

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text


def test_maximal_valid_values(client):
    payload = {
        "advanced": True, "anti_cheat_on": True, "bonus_frequency": 65535,
        "country": "a" * 2, "current_map": "a" * 16,
        "game_style": "a" * 3, "info": "a" * 255,
        "max_players": 1, "name": "a" * 30, "num_bots": 255,
        "os": "a" * 10, "players": ["p" * 16],
        "port": 65535, "private": True, "realistic": True,
        "respawn": 4_294_967_295, "survival": True, "version": "a" * 10,
        "wm": True,
    }

    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text


def test_invalid_json(client):
    resp = client.post(
        "/servers",
        content='{"name": "Test", "port":',
        headers={"content-type": "application/json"},
    )
    assert_error_response(resp, 400, "Invalid input")


@pytest.mark.parametrize(
    ("name", "field", "value"),
    [
        ("port as string", "port", "23073"),
        ("max_players as string", "max_players", "ten"),
        ("players as string", "players", "alice,bob"),
        ("advanced as string", "advanced", "yes"),
        ("bonus_frequency as negative number", "bonus_frequency", -1),
        ("respawn as negative number", "respawn", -1),
    ],
)
def test_invalid_json_types(client, name, field, value):
    payload = valid_register_payload(20900)
    payload[field] = value

    resp = client.post("/servers", json=payload)
    assert_error_response(resp, 400, "Invalid input")


def test_invalid_input_wrong_shape(client):
    resp = client.post("/servers", json={"some_value": "test"})
    assert_error_response(resp, 400, "Invalid input")


def test_x_forwarded_for_header_is_ignored(client):
    # A server can only register itself, not spoof another IP via a header
    payload = valid_register_payload(21050)
    resp = client.post(
        "/servers",
        json=payload,
        headers={"X-Forwarded-For": "255.255.255.255"},
    )
    assert resp.status_code == 201, resp.text

    real_ip = client.get("/servers/127.0.0.1/21050")
    assert real_ip.status_code == 200, real_ip.text
    assert real_ip.json()["ip"] == "127.0.0.1"

    spoofed_ip = client.get("/servers/255.255.255.255/21050")
    assert spoofed_ip.status_code == 404, spoofed_ip.text


def test_registration(client):
    payload = valid_register_payload(21000)
    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text

    get = client.get("/servers/127.0.0.1/21000")
    assert get.status_code == 200, get.text

    fields = get.json()
    for key in SERVER_FIELDS:
        assert key in fields, f"response missing field {key!r}"
    assert set(fields.keys()) == set(SERVER_FIELDS), fields
    assert "UpdatedAt" not in fields
    assert "updated_at" not in fields

    assert fields["ip"] == "127.0.0.1"
    assert fields["name"] == "Contract Test Server"
    assert fields["players"] == ["alice", "bob"]


def test_update(client):
    register_and_require_created(client, valid_register_payload(21100))

    updated = valid_register_payload(21100)
    updated["name"] = "Renamed Server"
    updated["current_map"] = "ctf_Snake"
    updated["players"] = ["charlie"]
    register_and_require_created(client, updated)

    get = client.get("/servers/127.0.0.1/21100")
    server = get.json()

    assert server["name"] == "Renamed Server"
    assert server["current_map"] == "ctf_Snake"
    assert server["players"] == ["charlie"]


def test_duplicate_ip_and_port(client):
    register_and_require_created(client, valid_register_payload(21200))
    register_and_require_created(client, valid_register_payload(21200))
    register_and_require_created(client, valid_register_payload(21200))

    servers = client.get("/servers").json()
    count = sum(1 for s in servers if s["ip"] == "127.0.0.1" and s["port"] == 21200)
    assert count == 1, f"found {count} entries for the same ip:port after 3 registrations"
