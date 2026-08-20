from pydantic import BaseModel

from features.servers.models.register_input import RegisterServerInput


class Server(BaseModel):
    """
    GET /servers and GET /servers/{ip}/{port} response shape

    Kept separate from RegisterServerInput: ip is set by the server, not
    the client, and there's no "updated_at" field exposed here
    """

    advanced: bool
    anti_cheat_on: bool
    bonus_frequency: int
    country: str
    current_map: str
    game_style: str
    ip: str
    info: str
    max_players: int
    name: str
    num_bots: int
    os: str
    players: list[str]
    port: int
    private: bool
    realistic: bool
    respawn: int
    survival: bool
    version: str
    wm: bool

    @classmethod
    def from_input(cls, input: RegisterServerInput, ip: str) -> "Server":
        return cls(**input.model_dump(), ip=ip)
