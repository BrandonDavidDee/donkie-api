# AGENTS.md

## Project snapshot
- `app/main.py` is the actual FastAPI app entrypoint; the root `main.py` is only a "Hello from donkie-api!" stub.
- `README.md` is the best source of product intent: a multi-tenant, API-first chat service with scoped JWT auth, no websockets, and no built-in user directory.
- `README.md` is populated and should be treated as the design reference alongside the code.

## Architecture to keep in mind
- The intended domain model is conversation-centric: `conversations`, `conversation_tags`, `participants`, `messages`, and `message_mentions` are the key concepts described in `README.md`.
- Every persisted domain table is expected to carry `tenant_id` for isolation; tag lookup and message access are designed around tenant-scoped queries.
- Auth is intentionally externalized: the host app mints JWTs with permissioned `scope` values (for example `assignment:882:read`, `assignment:882:write`, `assignment:882:tag`, `*:create`), and this service verifies the token against `app_keys`, enforces app/tenant prefix matching, then checks action-specific scope in controllers.

## Current codebase shape
- `app/schema.py` defines the core SQLAlchemy models (`App`, `AppKey`, `Conversation`, `ConversationTag`, `Participant`, `Message`, `MessageMention`) and is the migration source of truth.
- `app/main.py` wires lifespan DB pool startup/shutdown, CORS middleware, and routers from `app/root_route.py` and `app/conversations/routes.py`.
- `app/__init__.py` is empty; there is no package-level wiring to preserve.

## Migrations and configuration
- Alembic is configured for async PostgreSQL in `alembic/env.py` using `create_async_engine(..., poolclass=NullPool)`.
- Database connection settings come from environment variables loaded via `.env`: `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`, and `DATABASE_NAME`.
- `alembic.ini` points at `alembic/` for revision scripts, and `schema.Base.metadata` is the migration target.

## Local workflows
- Run the API with `uv run uvicorn app.main:app --reload`.
- Create/apply migrations with `uv run alembic revision --autogenerate -m "..."` and `uv run alembic upgrade head`.
- Type-check with `uv run pyright`; `pyrightconfig.json` includes `app/` and `tests/`, but there is no `tests/` directory yet.
- Run tests with `uv run pytest` if/when tests are added.

## Implementation conventions
- Keep new backend code under `app/`; keep schema changes mirrored in Alembic migrations.
- Prefer explicit, self-contained API responses, matching the schema notes' denormalized fields like `sender_display_name` and `mentioned_display_name`.
- Use composite keys and lookup indexes where the schema notes call for them, especially for tags and mentions.

## What to check before changing behavior
- Read `README.md` first when adding API, auth, or data-model work; it is the design authority for the intended chat service.
- Conversation endpoints in `app/conversations/routes.py` are implemented across list/detail/search/counts, tag/participant writes, and message create/list/update; follow the existing one-controller-per-endpoint pattern in `app/conversations/controllers/`.
- Avoid hard-coding database URLs or tenant/user semantics; those are intentionally environment- and token-driven.
