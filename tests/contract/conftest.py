import contextlib
import os
import socket
import threading
import time

import httpx
import pytest
import uvicorn

from app.main import create_app

EXTERNAL_BASE_URL = os.environ.get("SPP_LOBBY_BASE_URL", "").rstrip("/")


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _ServerThread(threading.Thread):
    def __init__(self, port: int):
        super().__init__(daemon=True)
        # proxy_headers=False: see app/__main__.py
        config = uvicorn.Config(
            create_app(), host="127.0.0.1", port=port, log_level="warning", proxy_headers=False
        )
        self.server = uvicorn.Server(config)

    def run(self) -> None:
        self.server.run()

    def stop(self) -> None:
        self.server.should_exit = True


@pytest.fixture
def live_server():
    """
    Base URL for a real, running server: an in-process uvicorn instance
    bound to a real TCP port, unless SPP_LOBBY_BASE_URL points elsewhere

    Each test gets its own fresh instance, no state shared between tests
    """
    if EXTERNAL_BASE_URL:
        yield EXTERNAL_BASE_URL
        return

    port = _free_port()
    thread = _ServerThread(port)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            httpx.get(f"{base_url}/servers", timeout=0.2)
            break
        except httpx.HTTPError:
            time.sleep(0.05)
    else:
        raise RuntimeError("server did not become ready in time")

    yield base_url

    thread.stop()
    thread.join(timeout=5)


@pytest.fixture
def client(live_server):
    with httpx.Client(base_url=live_server, timeout=10) as c:
        yield c
