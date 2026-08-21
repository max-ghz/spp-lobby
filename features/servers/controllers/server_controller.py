import json

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from features.servers.exceptions import ServerNotFoundError
from features.servers.models import RegisterServerInput, Server
from features.servers.services import ServerStorage
from shared.errors import error_response


def _parse_port(port: str) -> int | None:
    if not port.isdigit():
        return None
    value = int(port)
    if value > 65535:
        return None
    return value


async def register_server(request: Request, store: ServerStorage) -> JSONResponse:
    # Parsed manually, not via a Pydantic body param, so this works
    # regardless of the request's Content-Type header
    try:
        data = json.loads(await request.body())
        input = RegisterServerInput.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return error_response(400, "Invalid input")

    ip = request.client.host if request.client else ""
    store.register(ip, input)
    return JSONResponse(status_code=201, content={})


def list_servers(store: ServerStorage) -> list[Server]:
    return store.list()


def get_specific_server(ip: str, port: str, store: ServerStorage) -> Server | JSONResponse:
    parsed_port = _parse_port(port)
    if parsed_port is None:
        return error_response(400, "Invalid port")

    server = store.get(ip, parsed_port)
    if server is None:
        raise ServerNotFoundError(ip, parsed_port)

    return server


def get_players_of_server(ip: str, port: str, store: ServerStorage) -> list[str] | JSONResponse:
    parsed_port = _parse_port(port)
    if parsed_port is None:
        return error_response(400, "Invalid port")

    server = store.get(ip, parsed_port)
    if server is None:
        raise ServerNotFoundError(ip, parsed_port)

    return server.players
