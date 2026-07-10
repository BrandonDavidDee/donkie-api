# AGENTS.md

## Project snapshot
- `app/main.py` is the actual FastAPI app entrypoint; the root `main.py` is only a "Hello from donkie-api!" stub.
- `SCHEMA_NOTES.md` is the best source of product intent: a multi-tenant, API-first chat service with scoped JWT auth, no websockets, and no built-in user directory.
- `README.md` is currently a placeholder, so prefer the code and schema notes over the README for implementation details.

## Architecture to keep in mind
- The intended domain model is conversation-centric: `conversations`, `conversation_tags`, `participants`, `messages`, and `message_mentions` are the key concepts described in `SCHEMA_NOTES.md`.
- Every persisted domain table is expected to carry `tenant_id` for isolation; tag lookup and message access are designed around tenant-scoped queries.
- Auth is intentionally externalized: the host app mints JWTs with `scope` claims, and this service only verifies the token and compares requested tags/conversations against the scope.

## Current codebase shape
- `app/schema.py` currently defines only `AuthUser` and still references missing models (`SourceBucket`, `SourceVimeo`); treat it as incomplete/legacy skeleton code.
- `app/main.py` currently has only two toy routes (`/` and `/items/{item_id}`), so any real API work should happen by adding routers/modules rather than expanding these placeholder handlers.
- `app/__init__.py` is empty; there is no package-level wiring to preserve.

## Migrations and configuration
- Alembic is configured for async PostgreSQL in `alembic/env.py` using `create_async_engine(..., poolclass=NullPool)`.
- Database connection settings come from environment variables loaded via `.env`: `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, and `DATABASE_NAME`.
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
- Read `SCHEMA_NOTES.md` first when adding API, auth, or data-model work; it is the design authority for the intended chat service.
- Do not assume the current toy routes or `AuthUser` model represent the final architecture.
- Avoid hard-coding database URLs or tenant/user semantics; those are intentionally environment- and token-driven.

