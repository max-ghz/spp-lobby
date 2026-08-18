from tests.contract.helpers import assert_error_response, register_and_require_created, valid_register_payload


def test_existing(client):
    register_and_require_created(client, valid_register_payload(23001))

    resp = client.get("/servers/127.0.0.1/23001")

    assert resp.status_code == 200, resp.text
    assert "application/json" in resp.headers.get("content-type", "")
    server = resp.json()
    assert server["ip"] == "127.0.0.1"
    assert server["port"] == 23001


def test_not_found(client):
    resp = client.get("/servers/127.0.0.1/23099")
    assert_error_response(resp, 404, "server not found")


def test_invalid_port(client):
    resp = client.get("/servers/127.0.0.1/not-a-port")
    assert_error_response(resp, 400, "Invalid port")


def test_port_zero_not_registered(client):
    # Port 0 is a syntactically valid path param (unlike in the POST body,
    # where it's rejected as the zero value of a required field), so an
    # unregistered port 0 is a 404, not a 400
    resp = client.get("/servers/127.0.0.1/0")
    assert_error_response(resp, 404, "server not found")


def test_port_max_65535(client):
    register_and_require_created(client, valid_register_payload(65535))

    resp = client.get("/servers/127.0.0.1/65535")

    assert resp.status_code == 200, resp.text
    assert resp.json()["port"] == 65535


def test_port_out_of_range(client):
    resp = client.get("/servers/127.0.0.1/65536")
    assert_error_response(resp, 400, "Invalid port")
