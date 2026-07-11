from asyncpg import Record
from fastapi import APIRouter, Depends, HTTPException

from app.db import db

from .models import ConversationCreate, ConversationRead

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
    return ConversationRead(
        id=row["id"],
        title=row["title"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        archived_at=row["archived_at"],
    )
