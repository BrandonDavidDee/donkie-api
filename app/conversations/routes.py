from asyncpg import Record
from fastapi import APIRouter
from uuid import UUID

from app.db import db

from .models import ConversationCreate, ConversationRead, ConversationTagRead

router = APIRouter()


@router.post("")
async def conversation_create(payload: ConversationCreate) -> ConversationRead:
    query = "INSERT INTO conversations (tenant_id, title, created_by) VALUES ($1, $2, $3) RETURNING *"
    tenant_id = "foo:bar"
    created_by = "user:foo:1"
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
        tag_query = ("INSERT INTO conversation_tags "
                     "(conversation_id, tag_key, tag_value, tenant_id) "
                     "VALUES ($1, $2, $3, $4) RETURNING *")
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
async def get_conversations():
    query = """
    SELECT * FROM conversations c
    JOIN conversation_tags ct ON ct.conversation_id = c.id
    WHERE ct.tenant_id = $1 AND (ct.tag_key || ':' || ct.tag_value) = ANY($2)  
    """
    tenant_id = "foo:bar"
    tag = "event:123"
    values = (tenant_id, [tag])
    result: list[Record] = await db.select_many(query, values)
    output: list[UUID] = []
    for row in result:
        output.append(row["id"])
    return output