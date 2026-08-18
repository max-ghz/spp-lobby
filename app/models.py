from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_COUNTRY_LENGTH = 2
MAX_MAP_SIZE = 16
MAX_GAME_STYLE_SIZE = 3
MAX_INFO_SIZE = 255
MAX_NAME_SIZE = 30
MAX_OS_SIZE = 10
MAX_PLAYER_NAME_SIZE = 16
MAX_VERSION_SIZE = 10


class RegisterServerInput(BaseModel):
    """
    POST /servers request body

    country/info/bonus_frequency/num_bots/respawn just have to be present, so empty string or 0 is fine
    current_map/game_style/name/os/version/max_players/port reject their zero value
    strict=True rejects "23073"(string) for an int field
    """

    model_config = ConfigDict(strict=True, extra="ignore")

    advanced: bool
    anti_cheat_on: bool
    bonus_frequency: int = Field(ge=0, le=65535)
    country: str = Field(max_length=MAX_COUNTRY_LENGTH)
    current_map: str = Field(min_length=1, max_length=MAX_MAP_SIZE)
    game_style: str = Field(min_length=1, max_length=MAX_GAME_STYLE_SIZE)
    info: str = Field(max_length=MAX_INFO_SIZE)
    max_players: int = Field(gt=0, le=255)
    name: str = Field(min_length=1, max_length=MAX_NAME_SIZE)
    num_bots: int = Field(ge=0, le=255)
    os: str = Field(min_length=1, max_length=MAX_OS_SIZE)
    players: list[str]
    port: int = Field(gt=0, le=65535)
    private: bool
    realistic: bool
    respawn: int = Field(ge=0, le=4_294_967_295)
    survival: bool
    version: str = Field(min_length=1, max_length=MAX_VERSION_SIZE)
    wm: bool

    @model_validator(mode="after")
    def check_players(self) -> "RegisterServerInput":
        if len(self.players) > self.max_players:
            raise ValueError("too many players for max_players")
        for name in self.players:
            if len(name) > MAX_PLAYER_NAME_SIZE:
                raise ValueError("player name too long")
        return self


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
