REQUIRED_FIELDS = [
    "advanced",
    "anti_cheat_on",
    "bonus_frequency",
    "country",
    "current_map",
    "game_style",
    "info",
    "max_players",
    "name",
    "num_bots",
    "os",
    "players",
    "port",
    "private",
    "realistic",
    "respawn",
    "survival",
    "version",
    "wm",
]

SERVER_FIELDS = REQUIRED_FIELDS + ["ip"]


def valid_register_payload(port: int) -> dict:
    return {
        "advanced": False,
        "anti_cheat_on": False,
        "bonus_frequency": 10,
        "country": "PL",
        "current_map": "ctf_Ash",
        "game_style": "CTF",
        "info": "Contract test server",
        "max_players": 32,
        "name": "Contract Test Server",
        "num_bots": 1,
        "os": "Linux",
        "players": ["alice", "bob"],
        "port": port,
        "private": False,
        "realistic": False,
        "respawn": 1,
        "survival": False,
        "version": "1.0",
        "wm": False,
    }


def assert_error_response(resp, want_status: int, want_message: str) -> None:
    assert resp.status_code == want_status, resp.text
    assert "application/json" in resp.headers.get("content-type", ""), resp.headers
    body = resp.json()
    assert set(body.keys()) == {"message"}, body
    assert body["message"] == want_message


def register_and_require_created(client, payload: dict):
    resp = client.post("/servers", json=payload)
    assert resp.status_code == 201, resp.text
    return resp
