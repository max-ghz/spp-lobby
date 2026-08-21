from fastapi import APIRouter, Depends, Request

from features.servers import controllers
from features.servers.models import Server
from features.servers.services import ServerStorage

router = APIRouter(prefix="/servers")


def get_store(request: Request) -> ServerStorage:
    return request.app.state.store


@router.get("", response_model=list[Server])
def list_servers(store: ServerStorage = Depends(get_store)) -> list[Server]:
    return controllers.list_servers(store)


@router.post("", status_code=201)
async def register_server(request: Request, store: ServerStorage = Depends(get_store)):
    return await controllers.register_server(request, store)


@router.get("/{ip}/{port}")
def get_specific_server(ip: str, port: str, store: ServerStorage = Depends(get_store)):
    return controllers.get_specific_server(ip, port, store)


@router.get("/{ip}/{port}/players")
def get_players_of_server(ip: str, port: str, store: ServerStorage = Depends(get_store)):
    return controllers.get_players_of_server(ip, port, store)
