"""
Registers a sample server against a running spp-lobby instance
How to use:
    python scripts/register_test_server.py                                 # targets http://localhost:8000
    BASE_URL=http://localhost:6969 python scripts/register_test_server.py  # targets a different host/port
"""

import os

import httpx

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

payload = {
    "advanced": False,
    "anti_cheat_on": False,
    "bonus_frequency": 10,
    "country": "PL",
    "current_map": "kz_Mantra",
    "game_style": "CTF",
    "info": "kz_Mantra 24/7",
    "max_players": 32,
    "name": "Soldank++ Server",
    "num_bots": 1,
    "os": "Linux",
    "players": ["max-ghz", "nedik"],
    "port": 23073,
    "private": False,
    "realistic": False,
    "respawn": 1,
    "survival": False,
    "version": "1.0",
    "wm": False,
}

if __name__ == "__main__":
    resp = httpx.post(f"{BASE_URL}/servers", json=payload)
    print(resp.status_code, resp.text)
