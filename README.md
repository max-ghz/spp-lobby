# Soldank++ Lobby

[Soldank++](https://github.com/nedik/soldank-plus-plus) JSON API based lobby server. Enables registering and discovering all registered [Soldank++](https://github.com/nedik/soldank-plus-plus) servers.

## Endpoints
| HTTP Method | Endpoint                      | Returned type                      | Description                                                                                  |
| ----------- | ----------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| GET         |  `/servers`                   | List<[Server](app/models.py#L54)>  | Returns a list of all registered servers.                                                      |
| GET         |  `/servers/:ip/:port`         | [Server](app/models.py#L54)        | Returns information about a server specified by the given `ip` and `port`.                     |
| GET         |  `/servers/:ip/:port/players` | List<string>                       | Returns a list of players of a server specified by the given `ip` and `port`.                  |
| POST        |  `/servers`                   | Empty                               | Registers a new server. Requires [RegisterServerInput](app/models.py#L13) as request's body.   |

## Environment variables
- `PORT`: what to listen on when run directly (default 8000).
- `SERVER_EXPIRY_TIME_IN_SECONDS`: how long a server is kept without re-registering (default 300 = 5 minutes).

## Dependencies
The project uses the following packages:
- [FastAPI](https://fastapi.tiangolo.com/): Framework that handles HTTP connections and routing
- [Pydantic](https://docs.pydantic.dev/): Request/response validation and serialization
- [Uvicorn](https://uvicorn.dev/): ASGI server that runs the application

## Building
Make sure you have Python 3.12 (or higher) and clone this repository:
```bash
git clone git@github.com:max-ghz/spp-lobby.git
cd spp-lobby
```

Create a virtual environment and install development dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running

```bash
PORT=8000 python -m app
```

Then register a sample server:
```bash
python scripts/register_test_server.py
```

## Testing

### Unit tests
Unit tests cover `app/models.py` and `app/storage.py` directly.
```bash
pytest                                       # all tests
pytest --cov=app --cov-report=term-missing   # with coverage
```

### Contract tests
`tests/contract/` are black-box HTTP tests: they only talk to the API over real HTTP, not to internal Python types. Each test starts its own server, so no manual setup is needed.
```bash
pytest tests/contract/
```

Optionally, you can point them at a different, already-running server instead:
```bash
SPP_LOBBY_BASE_URL=http://put_real_server_here pytest tests/contract/
```

### Mutation testing
`mutmut` introduces small bugs into `app/` one at a time and reruns the tests, to check whether the tests actually catch real bugs and not just cover lines.
```bash
mutmut run
mutmut results
```