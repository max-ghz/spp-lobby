import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError

from app.models import RegisterServerInput, Server
from app.storage import ServerStore

FAVICON_PATH = Path(__file__).parent / "static" / "favicon.ico"


def _invalid_input() -> JSONResponse:
    return JSONResponse(status_code=400, content={"message": "Invalid input"})


def _parse_port(port: str) -> int | None:
    if not port.isdigit():
        return None
    value = int(port)
    if value > 65535:
        return None
    return value


def create_app() -> FastAPI:
    app = FastAPI()
    store = ServerStore()

    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Override FastAPI's default 422 + {"detail": [...]}
        return JSONResponse(status_code=400, content={"message": "Invalid input"})

    app.exception_handler(RequestValidationError)(validation_error_handler)

    def favicon() -> FileResponse:
        return FileResponse(FAVICON_PATH)

    app.get("/favicon.ico", include_in_schema=False)(favicon)

    def list_servers() -> list[Server]:
        return store.list()

    app.get("/servers", response_model=list[Server])(list_servers)

    async def register_server(request: Request):
        # Parsed manually, not via a Pydantic body param, so this works
        # regardless of the request's Content-Type header
        try:
            data = json.loads(await request.body())
            input = RegisterServerInput.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            return _invalid_input()

        ip = request.client.host if request.client else ""
        store.register(ip, input)
        return JSONResponse(status_code=201, content={})

    app.post("/servers", status_code=201)(register_server)

    def get_specific_server(ip: str, port: str):
        parsed_port = _parse_port(port)
        if parsed_port is None:
            return JSONResponse(status_code=400, content={"message": "Invalid port"})

        server = store.get(ip, parsed_port)
        if server is None:
            return JSONResponse(status_code=404, content={"message": "server not found"})

        return server

    app.get("/servers/{ip}/{port}")(get_specific_server)

    def get_players_of_server(ip: str, port: str):
        parsed_port = _parse_port(port)
        if parsed_port is None:
            return JSONResponse(status_code=400, content={"message": "Invalid port"})

        server = store.get(ip, parsed_port)
        if server is None:
            return JSONResponse(status_code=404, content={"message": "server not found"})

        return server.players

    app.get("/servers/{ip}/{port}/players")(get_players_of_server)

    return app


app = create_app()
