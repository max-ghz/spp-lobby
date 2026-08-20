# AGENTS.md

This file provides guidance to AI tools like Claude Code or Codex when working with code in this repository.

## Project

Python/FastAPI HTTP lobby server for Soldank++. Lets game servers register themselves and lets clients discover registered servers. No database. Everything lives in an in-memory dict guarded by a lock, with a TTL-based expiry sweep.

## Build

Requires Python 3.12+.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run it with `PORT=8000 python -m app`. Config is env vars only: `PORT` (listen port) and `SERVER_EXPIRY_TIME_IN_SECONDS` (registration TTL, default 300).

## Tests

`pytest`, driven by `pytest-cov` for coverage and `mutmut` for mutation testing.

```
pytest                                       # all tests
pytest --cov --cov-branch --cov-report=term-missing
mutmut run && mutmut results
```

Two kinds of tests:
- **`tests/test_models.py`, `tests/test_server_storage.py`**: unit tests against `features/servers/models/` and `features/servers/services/server_storage.py` directly.
- **`tests/contract/`**: black-box HTTP tests. Each test spins up its own `uvicorn` instance on a free port (see `tests/contract/conftest.py`) and talks to it only over real HTTP, never importing internal types. Point them at an already-running server instead with `SPP_LOBBY_BASE_URL=http://host:port pytest tests/contract/`.

Contract tests are the source of truth for API behavior. If they conflict with a unit test's assumptions, the contract tests win.

## Architecture

Feature-based: `app/main.py` is a composition root, business logic lives in `features/<feature>/`, and `shared/` holds only logic genuinely independent of any feature.

- **`app/main.py`**: creates the `FastAPI` app (`create_app()`), registers the global `RequestValidationError` handler and `/favicon.ico`, and mounts each feature's router. No business logic here by design. The `RequestValidationError` handler is dead code kept as a safety net; nothing triggers it in practice, since `register_server` validates the body manually.
- **`features/servers/`**: the only feature today. Owns everything about registering and discovering game servers.
  - **`routes.py`**: `create_router(store)` builds the `APIRouter` for all four endpoints and wires each one to `controllers/`.
  - **`controllers/`**: the use cases (`register_server`, `list_servers`, `get_specific_server`, `get_players_of_server`). `register_server` parses the body manually with `json.loads(await request.body())` instead of a Pydantic body parameter, so it works regardless of the request's `Content-Type` header.
  - **`models/`**: `RegisterServerInput` (request body, `strict=True`, `extra="ignore"`) and `Server` (response shape) are kept as separate classes on purpose: `ip` is server-assigned, not client-supplied, and `Server` has no `updated_at` field to expose.
  - **`services/server_storage.py`**: `ServerStorage`, one `dict[(ip, port), _Entry]` behind one `threading.Lock`. `register()` always does `pop(key, None)` before re-inserting so an update moves the entry to the end of iteration order. Expiry is a lazy sweep on every `get()`/`list()` call, not a background thread.
  - A feature must never import another feature's internals directly (`features.<other>.controllers`, `.services`, or non-public models). If a future feature needs data from `servers`, go through its public interface (`features/servers/__init__.py`), a `shared/` abstraction if the logic is truly domain-independent, or an event if the dependency is one-way and optional. Don't reach for an event when a plain call through the public interface is simpler.
- **`shared/errors.py`**: `error_response(status_code, message)`, the `{"message": ...}` envelope used for every error response. Holds zero domain knowledge on purpose, so it's safe to share across any future feature.
- **`app/__main__.py`**: `python -m app` entrypoint, calls `uvicorn.run("app.main:app", ..., proxy_headers=False)`. That flag is deliberate: uvicorn defaults to trusting `X-Forwarded-For` from `127.0.0.1`, which would let a client spoof its registered IP.
- **`app/static/favicon.ico`**: a static asset, not code.

## Code style

Comments should be short and only where they add real value:
- Delete comments that just restate what the code obviously does.
- No section-divider comments (e.g. `# --- section ---`).
- No meta-commentary about the coding process ("Note: I decided to...").
- Don't reference other files, languages, or implementations that might not exist in this repo. Keep comments self-contained.
- A single-sentence comment should not end with a trailing period. Only use periods when a comment has multiple distinct sentences.
- Do keep short explanations of genuinely non-obvious behavior or the root cause of a workaround (e.g. the `proxy_headers=False` line above).

Never use em-dashes (—) or a hyphen as sentence punctuation (word - word), anywhere: code, comments, docs, commit messages. Use a comma, period, colon, or parentheses instead. Hyphens inside compound words and identifiers (`in-memory`, `single-sentence`, `spp-lobby`) are fine.

Git commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `style:`), short and in imperative mood. No `Co-Authored-By` trailer.