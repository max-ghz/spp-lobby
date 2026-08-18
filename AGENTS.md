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
pytest --cov=app --cov-branch --cov-report=term-missing
mutmut run && mutmut results
```

Two kinds of tests:
- **`tests/test_models.py`, `tests/test_storage.py`**: unit tests against `app/models.py` and `app/storage.py` directly.
- **`tests/contract/`**: black-box HTTP tests. Each test spins up its own `uvicorn` instance on a free port (see `tests/contract/conftest.py`) and talks to it only over real HTTP, never importing internal types. Point them at an already-running server instead with `SPP_LOBBY_BASE_URL=http://host:port pytest tests/contract/`.

Contract tests are the source of truth for API behavior. If they conflict with a unit test's assumptions, the contract tests win.

## Architecture

Everything lives under `app/`:

- **`main.py`**: the FastAPI app and all four routes (`create_app()`). `POST /servers` parses the body manually with `json.loads(await request.body())` instead of a Pydantic body parameter, so it works regardless of the request's `Content-Type` header. The `RequestValidationError` handler is dead code kept as a safety net; nothing triggers it in practice.
- **`models.py`**: Pydantic models. `RegisterServerInput` (request body, `strict=True`, `extra="ignore"`) and `Server` (response shape) are kept as separate classes on purpose: `ip` is server-assigned, not client-supplied, and `Server` has no `updated_at` field to expose.
- **`storage.py`**: `ServerStore`: one `dict[(ip, port), _Entry]` behind one `threading.Lock`. `register()` always does `pop(key, None)` before re-inserting so an update moves the entry to the end of iteration order. Expiry is a lazy sweep on every `get()`/`list()` call, not a background thread.
- **`__main__.py`**: `python -m app` entrypoint, calls `uvicorn.run(..., proxy_headers=False)`. That flag is deliberate: uvicorn defaults to trusting `X-Forwarded-For` from `127.0.0.1`, which would let a client spoof its registered IP.

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