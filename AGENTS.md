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

Run it with `PORT=8000 python -m app`. Config is env vars only: `PORT` (listen port), `SERVER_EXPIRY_TIME_IN_SECONDS` (registration TTL, default 300), `RATE_LIMIT_BASE_DELAY_SECONDS` (registration throttling's first escalation tier, default 10, 0 disables it) and `RATE_LIMIT_RESET_SECONDS` (how long a quiet ip before its throttling state resets, default 300).

A `Dockerfile` is also available for building and running the app as a container, for hosting; it's not used for development or the test/lint tooling below, which all run against the venv.

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

If you need to know project's architecture, analyze it from the file: ARCHITECTURE.md.

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