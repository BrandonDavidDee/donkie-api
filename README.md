# donkie-api

A multi-tenant, API-first chat service. Context-agnostic, no websockets, no built-in user directory.

## Core Design Principles

- **Context-agnostic.** The service has no concept of events, assignments, clients, or staff. Everything domain-specific is expressed as tags applied by the host application.
- **No built-in users.** Only opaque `user_id` strings, scoped by `tenant_id`. Authorization ("is this staff member on this event") happens entirely in the host app, before a token is ever issued.
- **No realtime infrastructure.** No websockets, no presence tracking, no Redis. Polling or SSE is sufficient.
- **Multi-tenant from day one.** Every table carries `tenant_id` so multiple installing apps can share the service without collision.
- **Auth via scoped JWTs.** The host app mints short-lived signed tokens with a `scope` claim (tags or conversation IDs the bearer may access). This service only verifies the signature and compares requested resources against the scope — it never re-derives business rules.

---

## Local Development

**Prerequisites:** [uv](https://github.com/astral-sh/uv), PostgreSQL, a `.env` file (see below).

```bash
# Run the API (hot-reload)
uv run uvicorn app.main:app --reload

# Generate a migration after changing app/schema.py
uv run alembic revision --autogenerate -m "describe your change"

# Apply pending migrations
uv run alembic upgrade head

# Type-check
uv run pyright

# Run tests
uv run pytest
```

### Environment variables (`.env`)

```
DATABASE_USERNAME=...
DATABASE_PASSWORD=...
DATABASE_HOST=...
DATABASE_NAME=...
```

---

## Data Model

Five tables. `app/schema.py` contains the SQLAlchemy models; Alembic migrations live in `alembic/versions/`.

### `conversations`
The core object. No domain-specific fields — everything about context lives in `conversation_tags`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `tenant_id` | TEXT NOT NULL | Owning app/org |
| `title` | TEXT | Nullable UI label |
| `created_by` | TEXT NOT NULL | Opaque `user_id`, not a FK |
| `created_at` | TIMESTAMPTZ | Default `now()` |
| `archived_at` | TIMESTAMPTZ | Nullable — soft delete/close |

Index: `(tenant_id)`

### `conversation_tags`
The generic context layer. A conversation can carry any number of tags (e.g. `event:4291`, `date:2026-08-14`, `assignment:882`). This replaces a rigid `context_type/context_id` column and enables hierarchy and multi-context.

| Column | Type | Notes |
|---|---|---|
| `conversation_id` | UUID FK → conversations | Cascade delete |
| `tag_key` | TEXT NOT NULL | e.g. `"event"`, `"date"` |
| `tag_value` | TEXT NOT NULL | e.g. `"4291"`, `"2026-08-14"` |
| `tenant_id` | TEXT NOT NULL | Denormalized for fast scoped lookups |
| `created_at` | TIMESTAMPTZ | Default `now()` |

Primary key: `(conversation_id, tag_key, tag_value)` — prevents duplicates and makes existence checks a single lookup.  
Index: `(tenant_id, tag_key, tag_value)` — the critical path for "all conversations with tag X for tenant Y".

### `participants`
Membership/roster data — distinct from JWT scope. Used for read receipts, member lists, and notification targeting.

| Column | Type | Notes |
|---|---|---|
| `conversation_id` | UUID FK → conversations | Cascade delete |
| `user_id` | TEXT NOT NULL | Opaque, defined by host app |
| `tenant_id` | TEXT NOT NULL | |
| `last_read_at` | TIMESTAMPTZ | Null = never read |
| `joined_at` | TIMESTAMPTZ | Default `now()` |

Primary key: `(conversation_id, user_id)`  
Index: `(tenant_id, user_id)`

### `messages`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `conversation_id` | UUID FK → conversations | Cascade delete |
| `tenant_id` | TEXT NOT NULL | |
| `sender_id` | TEXT NOT NULL | Opaque `user_id` |
| `sender_display_name` | TEXT NOT NULL | Snapshot at send-time |
| `body` | TEXT NOT NULL | Stores mentions as `@[user_id]` tokens |
| `created_at` | TIMESTAMPTZ | Default `now()` |
| `edited_at` | TIMESTAMPTZ | Nullable |
| `deleted_at` | TIMESTAMPTZ | Nullable — soft delete, keeps thread intact |

`sender_display_name` is denormalized so API responses are self-contained — no second lookup needed by any consumer.  
Index: `(conversation_id, created_at)` — the hot path for paginated message fetches.

### `message_mentions`
Structured record of `@mentions`. Avoids re-parsing body text to answer "who was mentioned" or "what am I mentioned in." Indexed for unread-mention counts and notification routing.

| Column | Type | Notes |
|---|---|---|
| `message_id` | UUID FK → messages | Cascade delete |
| `user_id` | TEXT NOT NULL | Same id space as `participants.user_id` |
| `tenant_id` | TEXT NOT NULL | |
| `mentioned_display_name` | TEXT NOT NULL | Snapshot at send-time |
| `created_at` | TIMESTAMPTZ | Default `now()` |

Primary key: `(message_id, user_id)`  
Index: `(tenant_id, user_id)` — drives "everything I've been @mentioned in" queries.

**Mention body format:** store `@[user_id]` tokens in `body`, not raw display names. The frontend renders them as `@Jordan` using `mentioned_display_name` from the mentions array. This keeps the body stable if a display name changes after send.

**Autocomplete source:** scope to existing `participants` for the conversation — no separate user-search feature needed, and avoids surfacing a broader company-wide directory.

---

## Authorization Model

### How it works

One check, runs identically on every request:

1. Verify JWT signature and expiry.
2. Read the `scope` claim from the token.
3. Compare `scope` against the requested tag or conversation's stored tags.
4. Allow on match → `403` if not.

The route logic never changes per conversation — only the values being compared.

| Request type | What's compared | Match source |
|---|---|---|
| List by tag | requested `tag` param vs. token `scope` | query string |
| Single conversation (read/write) | conversation's stored tags vs. token `scope` | DB lookup on `conversation_tags` |
| Batched/hierarchical list | multiple requested tags vs. token `scope` | query string (multiple values) |

### JWT payload (minted by the host app)

```json
{
  "tenant_id": "events-app",
  "user_id": "staff_4471",
  "scope": ["assignment:882"],
  "exp": 1735689600
}
```

Token issuance is the **only** place business-rule authorization happens. The chat service never re-derives it.

### Example: authorized request

```http
GET /conversations?tag=assignment:882
Authorization: Bearer <token with scope=["assignment:882"]>
```
→ `200 OK`

### Example: unauthorized request

```http
GET /conversations?tag=event:4291
Authorization: Bearer <token with scope=["assignment:882"]>
```
→ `403 Forbidden` — the client must request a new token from the host app scoped to `event:4291`.

### Example: write to a conversation

```http
POST /conversations/9231/messages
Authorization: Bearer <token>

{ "body": "Running about 15 min behind, on my way now." }
```

Server looks up conversation `9231`'s stored tags, checks intersection with the token `scope`. Non-empty → `201 Created`.

### Example: batched/hierarchical lookup

A token can cover multiple tags, letting a single request span a context hierarchy:

```json
{ "scope": ["event:4291", "date:2026-08-14"] }
```

```http
GET /conversations?tag=event:4291&tag=date:2026-08-14
```

Returns all conversations matching either tag; each conversation includes its own `tags` array so the frontend can visually separate levels.

---

## Design Decisions

**Why `tenant_id` is on every table** — every query pattern needs to be tenant-scoped, and denormalizing it means every index can lead with `tenant_id` without requiring a join back to `conversations` to enforce the boundary.

**Why tags use a composite PK** — `(conversation_id, tag_key, tag_value)` prevents duplicate tags and makes "does this conversation have tag X" a straightforward existence check.

**Why there's no `read_receipts` table** — `last_read_at` per participant is enough to count unread messages (`COUNT WHERE created_at > last_read_at`). Per-message receipts can be added later if a real use case emerges.

**What's deliberately absent:**
- No `users` table — opaque IDs only.
- No `attachments` table — easy to bolt on later.
- No presence/online-status — no ephemeral state at all; everything is durable rows.

---

## Open Questions

- **Archival behavior:** should `archived_at` exclude conversations from tag-based list queries by default, or only when explicitly filtered?
- **Cleanup contract:** deleting a host-app domain object (e.g. an event) must explicitly call `DELETE /conversations?tag=event:4291` — this should be part of the documented API contract to avoid orphaned conversations.
- **JWT scope shape:** explicit conversation IDs (`conversation:9231`) vs. tag patterns (`tag:assignment:882`)? Tag-based scope avoids re-minting on every new conversation under an already-authorized context.
- **Auth pluggability:** token verification should be swappable (host app service credential today; first-party login later) without touching conversation/tag/message logic.
- **Mention permissions:** restrict `@mentions` to existing participants (simpler), or auto-add mentioned users as participants (Slack-like, but has authorization implications for `POST /messages`)?
- **Notification webhooks:** `message.created` payload should include the `mentions` array so the host app can distinguish mention-urgency from general conversation activity.
