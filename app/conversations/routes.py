from uuid import UUID

from asyncpg import Record
from fastapi import APIRouter, Depends, HTTPException, Query

from app.authorization.claims import TokenClaims, get_token_claims
from app.db import db

from .controllers.conversation import ConversationDetail
from .models import (
    ConversationCreate,
    ConversationRead,
    ConversationTagRead,
    MessageCreate,
    MessageRead,
)

router = APIRouter()


@router.post("")
async def conversation_create(
    payload: ConversationCreate, claims: TokenClaims = Depends(get_token_claims)
) -> ConversationRead:
    query = "INSERT INTO conversations (tenant_id, title, created_by) VALUES ($1, $2, $3) RETURNING *"
    tenant_id = claims["tenant_id"]
    created_by = claims["user_id"]
    row: Record = await db.insert(
        query,
        (
            tenant_id,
            payload.title,
            created_by,
        ),
    )
    conversation_id = row["id"]
    new_tags: list[ConversationTagRead] = []
    for tag in payload.tags:
        tag_query = (
            "INSERT INTO conversation_tags "
            "(conversation_id, tag_key, tag_value, tenant_id) "
            "VALUES ($1, $2, $3, $4) RETURNING *"
        )
        tag_values = (conversation_id, tag.tag_key, tag.tag_value, tenant_id)
        tag_row: Record = await db.insert(tag_query, tag_values)
        new_tag = ConversationTagRead(
            tag_key=tag_row["tag_key"],
            tag_value=tag_row["tag_value"],
            created_at=tag_row["created_at"],
        )
        new_tags.append(new_tag)

    return ConversationRead(
        id=conversation_id,
        title=row["title"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        archived_at=row["archived_at"],
        tags=new_tags,
    )


@router.get("")
async def get_conversations(
    tags: list[str] = Query(), claims: TokenClaims = Depends(get_token_claims)
):
    return await ConversationDetail(claims).get_conversations(tags)


@router.post("/{conversation_id}/messages")
async def post_message(
    conversation_id: UUID,
    payload: MessageCreate,
    claims: TokenClaims = Depends(get_token_claims),
) -> MessageRead:
    tag_query = (
        "SELECT * FROM conversation_tags WHERE tenant_id = $1 AND conversation_id = $2"
    )
    tenant_id = claims["tenant_id"]
    sender_id = claims["user_id"]
    results = await db.select_many(
        tag_query,
        (
            tenant_id,
            conversation_id,
        ),
    )

    if not results:
        raise HTTPException(404, "No Matching Conversation")

    tags = [f"{row["tag_key"]}:{row["tag_value"]}" for row in results]
    for t in tags:
        if t not in claims["scope"]:
            raise HTTPException(403, f"Scope does not permit tag '{t}'")

    # insert into messages logic here
    query = (
        "INSERT INTO messages "
        "(conversation_id, parent_message_id, tenant_id, sender_id, sender_display_name, body) "
        "VALUES ($1, $2, $3, $4, $5, $6) "
        "RETURNING *"
    )

    values = (
        conversation_id,
        None,
        tenant_id,
        sender_id,
        payload.sender_display_name,
        payload.body,
    )
    row: Record = await db.insert(query, values)

    return MessageRead(
        id=row["id"],
        sender_display_name=row["sender_display_name"],
        body=row["body"],
        reply_count=row["reply_count"],
        created_at=row["created_at"],
        edited_at=row["edited_at"],
        deleted_at=row["deleted_at"],
    )
