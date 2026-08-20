# Architecture

The app is organized by feature (domain), not by technical layer. `app/main.py` is a composition root: it creates the FastAPI app and wires features together, nothing else.

## Adding a new feature

Create `features/<feature>/` with only what it actually needs:
- `routes.py`: HTTP endpoints, wired to `controllers/`.
- `controllers/`: use-case functions, the feature's business/application logic.
- `models/`: the feature's own Pydantic models.
- `services/`: only if the feature needs its own state, storage, or domain rules beyond validation.

Don't create empty `services/`, `repositories/`, or `events.py` a feature doesn't need yet.

Wire it into the app from `app/main.py`, by importing the feature's router factory and mounting it with `app.include_router(...)`.

## Where things go

- **New route** goes in `features/<feature>/routes.py`. It should only parse the HTTP request, call a controller, and return the result. No `try`/`except`, no other control flow, no direct calls to a service.
- **New controller** goes in `features/<feature>/controllers/`. Request validation, orchestration, and calls into `services/` happen here.
- **New model** goes in `features/<feature>/models/`, in the feature whose domain it represents. A model doesn't move to `shared/` just because another feature could technically import it.

## When to use `shared/`

Only for logic genuinely independent of any single domain, like `shared/errors.py`'s HTTP error envelope. Ask: does this code know anything about a specific feature's domain concepts? If yes, it stays in that feature.

## When to use an event instead of a direct call

Only when feature A needs to announce that something happened, and feature B is free to react to it (or not) without A knowing or caring whether B exists. If A needs feature B's data right now to do its own job, that's a direct dependency, use B's public interface instead. Don't build an event for something a plain function call already solves.

## What must never be imported

A feature must never reach into another feature's internals:
```
from features.<other>.controllers import ...
from features.<other>.services import ...
from features.<other>.models.something import ...
```
The only sanctioned way to depend on another feature is through its public interface, `features/<other>/__init__.py`.

`shared/` must never import from `features/`.

`app/main.py` may import a feature's `routes.py` (to mount it) and `services` (to construct state and inject it), but never a feature's `controllers/` or `models/`, that would put business logic into the composition root.

`tests/test_architecture.py` enforces these rules automatically on every test run.
