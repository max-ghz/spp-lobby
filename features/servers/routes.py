from fastapi import APIRouter, Request

from features.servers import controllers
from features.servers.models import Server
from features.servers.services import ServerStorage


def create_router(store: ServerStorage) -> APIRouter:
    router = APIRouter()

    def list_servers() -> list[Server]:
        return controllers.list_servers(store)

    router.get("/servers", response_model=list[Server])(list_servers)

    async def register_server(request: Request):
        return await controllers.register_server(request, store)

    router.post("/servers", status_code=201)(register_server)

    def get_specific_server(ip: str, port: str):
        return controllers.get_specific_server(ip, port, store)

    router.get("/servers/{ip}/{port}")(get_specific_server)

    def get_players_of_server(ip: str, port: str):
        return controllers.get_players_of_server(ip, port, store)

    router.get("/servers/{ip}/{port}/players")(get_players_of_server)

    return router
