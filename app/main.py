from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from features.servers.exceptions import ServerLimitExceededError, ServerNotFoundError
from features.servers.routes import router
from features.servers.services import ServerStorage
from shared.errors import error_response

FAVICON_PATH = Path(__file__).parent / "static" / "favicon.ico"


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.store = ServerStorage()

    # app doesn't exist until this factory runs, so handlers here use explicit
    # registration instead of @decorator syntax (see ARCHITECTURE.md)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(400, "Invalid input")

    app.exception_handler(RequestValidationError)(validation_error_handler)

    async def server_not_found_handler(request: Request, exc: ServerNotFoundError) -> JSONResponse:
        return error_response(404, "server not found")

    app.exception_handler(ServerNotFoundError)(server_not_found_handler)

    async def server_limit_exceeded_handler(request: Request, exc: ServerLimitExceededError) -> JSONResponse:
        return error_response(429, "too many servers registered for this ip")

    app.exception_handler(ServerLimitExceededError)(server_limit_exceeded_handler)

    def favicon() -> FileResponse:
        return FileResponse(FAVICON_PATH)

    app.get("/favicon.ico", include_in_schema=False)(favicon)

    app.include_router(router)

    return app


app = create_app()
