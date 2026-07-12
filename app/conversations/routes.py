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
    # TODO: automatically add creator as participant
    return await ConversationCreateControl(claims).conversation_create(payload)


@router.get("")
async def conversation_list(
    tags: list[str] = Query(), claims: TokenClaims = Depends(get_token_claims)
) -> list[ConversationRead]:
    return await ConversationListControl(claims).conversation_list(tags)


@router.get("/{conversation_id}")
async def conversation_detail():
    # TODO: Here, we grab the full conversation detail, participant list and first x amount of messages
    pass


@router.post("/{conversation_id}/participants")
async def participant_create():
    # TODO: build this out
    pass


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
    # TODO: This will eventually be used to grab the NEXT x amount of messages, appending
    # to what is initially loaded in conversation detail
    return await MessageListControl(claims, conversation_id).message_list()
