from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.authorization.claims import TokenClaims, get_token_claims

from .controllers.conversation_create import ConversationCreateControl
from .controllers.conversation_list import ConversationListControl
from .controllers.message_create import MessageCreateControl
from .controllers.message_list import MessageListControl
from .models.conversation import (
    ConversationCreate,
    ConversationRead,
)
from .models.message import (
    MessageCreate,
    MessageRead,
)

router = APIRouter()


@router.post("")
async def conversation_create(
    payload: ConversationCreate, claims: TokenClaims = Depends(get_token_claims)
) -> ConversationRead:
    return await ConversationCreateControl(claims).conversation_create(payload)


@router.get("")
async def conversation_list(
    tags: list[str] = Query(), claims: TokenClaims = Depends(get_token_claims)
) -> list[ConversationRead]:
    return await ConversationListControl(claims).conversation_list(tags)


@router.post("/{conversation_id}/messages")
async def message_create(
    conversation_id: UUID,
    payload: MessageCreate,
    claims: TokenClaims = Depends(get_token_claims),
) -> MessageRead:
    return await MessageCreateControl(claims, conversation_id).message_create(payload)


@router.get("/{conversation_id}/messages")
async def message_list(
    conversation_id: UUID,
    claims: TokenClaims = Depends(get_token_claims),
) -> list[MessageRead]:
    return await MessageListControl(claims, conversation_id).message_list()
