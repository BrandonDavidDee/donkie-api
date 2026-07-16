# donkie-api

`donkie-api` is a multi-tenant chat backend built with FastAPI and PostgreSQL.

It is intentionally:
- context-agnostic (domain meaning lives in tags)
- API-first (no websocket infrastructure)
- externally authenticated (host app mints JWTs)
- user-directory-free (only opaque `user_id` values)

## Quick start

### Prerequisites

- [uv](https://github.com/astral-sh/uv)
- PostgreSQL
- A `.env` file

### Minimal `.env`

```bash
DATABASE_USERNAME=...
DATABASE_PASSWORD=...
DATABASE_HOST=...
DATABASE_PORT=5432
DATABASE_NAME=...
```

Optional CORS settings used by `app/main.py`:

```bash
ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
ALLOW_ORIGIN_REGEX=
```

### Run locally

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Dev checks

```bash
uv run pyright
uv run pytest
```

## High-level architecture

### Runtime entrypoints

- `app/main.py`: real FastAPI app (lifespan, DB pool, middleware, routers)
- `main.py`: simple local stub (`Hello from donkie-api!`)

### HTTP surface

- `app/root_route.py`: health-ish root response and token echo endpoint
- `app/conversations/routes.py`: conversation/tag/participant/message APIs

### Persistence

- `app/db.py`: asyncpg pool + thin query helpers
- `app/schema.py`: SQLAlchemy metadata used as Alembic source of truth
- `alembic/versions/`: migration history

## Project structure

```text
app/
  main.py                  # app factory + CORS + router registration
  root_route.py            # GET / and GET /whoami
  db.py                    # asyncpg pool and query helpers
  conf.py                  # environment loading
  schema.py                # SQLAlchemy models / metadata
  authorization/
    claims.py              # JWT parsing + key lookup + tenant/app checks
  conversations/
    routes.py              # endpoint declarations
    controllers/           # one controller per endpoint/use-case
    models/                # Pydantic request/response models
alembic/
  env.py                   # async Alembic configuration
  versions/                # migration scripts
```

## Data model (current implementation)

Core tables live in `app/schema.py` and currently include:
- `apps` and `app_keys` for token verification
- `conversations`
- `conversation_tags`
- `participants`
- `messages`
- `message_mentions`

Important modeling choices reflected in code:
- every domain table is tenant-scoped via `tenant_id`
- tags use composite PK: `(conversation_id, tag_key, tag_value)`
- participants use composite PK: `(conversation_id, user_id)`
- mentions use composite PK: `(message_id, user_id)`
- messages include `parent_message_id` and `reply_count` columns (threading-oriented schema fields)

## Authorization and scope model

The host application mints JWTs. This service does not decide business authorization rules.

At request time, `app/authorization/claims.py` does three key checks:
1. Resolve `kid` from JWT header and fetch public key from `app_keys`
2. Verify signature/expiry
3. Enforce app isolation: `tenant_id` must start with `<app_id>:`

Controllers then enforce action-specific scope using `BaseController` (`app/base_controller.py`):
- wildcard example: `*:read`
- tag+action examples: `assignment:882:read`, `assignment:882:write`, `assignment:882:create`, `assignment:882:tag`, `assignment:882:manage_participants`

### Token claim shape expected by code

```json
{
  "tenant_id": "events-app:acme",
  "user_id": "staff_4471",
  "display_name": "Jordan",
  "scope": ["assignment:882:read", "assignment:882:write"],
  "exp": 1735689600
}
```

## API overview

Conversation routes are mounted under `/conversations`.

### Root/auth utilities

- `GET /` returns service metadata and current alembic version
- `GET /whoami` returns decoded claims for the bearer token

### Conversation endpoints

- `POST /conversations`
- `GET /conversations` (tag-filtered list with cursor/limit)
- `POST /conversations/counts`
- `POST /conversations/search`
- `GET /conversations/{conversation_id}`
- `POST /conversations/{conversation_id}/tags`
- `POST /conversations/{conversation_id}/participants`
- `POST /conversations/{conversation_id}/messages`
- `GET /conversations/{conversation_id}/messages`
- `PUT /conversations/{conversation_id}/messages/{message_id}`

For concrete payload/response shapes, check Pydantic models in `app/conversations/models/`.

## How contributors should work in this repo

### Typical backend change flow

1. Update or add logic under `app/` (usually a controller + model update)
2. If schema changed, update `app/schema.py`
3. Generate migration:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

4. Apply migrations locally:

```bash
uv run alembic upgrade head
```

5. Run checks:

```bash
uv run pyright
uv run pytest
```

### Conventions already used in code

- one-controller-per-endpoint/use-case in `app/conversations/controllers/`
- query-layer logic is mostly explicit SQL via `db` helpers
- API responses favor self-contained fields (for example `sender_display_name`)

## Notes for curious readers

- There is no websocket server in this project; clients are expected to poll (or use SSE externally).
- There is no first-party user table; identity and membership semantics come from host-issued tokens and participant rows.
- `README` design ideas may evolve, but implementation details should be verified against code under `app/` when contributing.
