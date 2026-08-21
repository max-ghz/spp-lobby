import time

from tests.contract.helpers import assert_error_response, register_and_require_created, valid_register_payload


def test_first_three_registrations_are_never_throttled(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "5")
    for i in range(3):
        register_and_require_created(client, valid_register_payload(26000 + i))


def test_fourth_registration_is_throttled(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "5")
    for i in range(3):
        register_and_require_created(client, valid_register_payload(26100 + i))

    resp = client.post("/servers", json=valid_register_payload(26103))
    assert_error_response(resp, 429, "too many registration attempts, slow down")
    assert resp.headers.get("retry-after") == "5"


def test_registration_succeeds_once_the_tier_delay_elapses(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "1")
    for i in range(3):
        register_and_require_created(client, valid_register_payload(26200 + i))

    blocked = client.post("/servers", json=valid_register_payload(26203))
    assert_error_response(blocked, 429, "too many registration attempts, slow down")

    time.sleep(1.1)
    register_and_require_created(client, valid_register_payload(26203))


def test_rejected_retries_do_not_push_the_wait_further_out(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "1")
    for i in range(3):
        register_and_require_created(client, valid_register_payload(26300 + i))

    first = client.post("/servers", json=valid_register_payload(26303))
    time.sleep(0.3)
    second = client.post("/servers", json=valid_register_payload(26303))

    assert first.status_code == 429, first.text
    assert second.status_code == 429, second.text
    assert int(second.headers["retry-after"]) <= int(first.headers["retry-after"])


def test_idle_ip_gets_a_clean_slate(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BASE_DELAY_SECONDS", "5")
    monkeypatch.setenv("RATE_LIMIT_RESET_SECONDS", "1")
    for i in range(3):
        register_and_require_created(client, valid_register_payload(26400 + i))

    blocked = client.post("/servers", json=valid_register_payload(26403))
    assert_error_response(blocked, 429, "too many registration attempts, slow down")

    time.sleep(1.1)  # ip's been quiet longer than the reset window now, so it's fresh again

    register_and_require_created(client, valid_register_payload(26404))
    register_and_require_created(client, valid_register_payload(26405))
    register_and_require_created(client, valid_register_payload(26406))
