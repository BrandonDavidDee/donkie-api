from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.authorization.claims import TokenClaims, get_token_claims

from .controllers.conversation_counts import (
    ConversationCountsControl,
    ConversationCountsPayload,
)
from .controllers.conversation_create import ConversationCreateControl
from .controllers.conversation_detail import ConversationDetailControl
from .controllers.conversation_list import ConversationListControl
from .controllers.conversation_search import (
    ConversationSearchControl,
    ConversationSearchPayload,
)
from .controllers.message_create import MessageCreateControl
from .controllers.message_list import MessageListControl
from .controllers.message_pagination import MessageSortOrder
from .controllers.message_update import MessageUpdateControl
from .controllers.participant_create import ParticipantCreateControl
from .controllers.tag_create import TagCreateControl
from .models.conversation import (
    ConversationCreate,
    ConversationListPaginated,
    ConversationRead,
)
from .models.message import (
    MessageCreate,
    MessageListPaginated,
    MessageRead,
    MessageUpdate,
)
from .models.participant import ParticipantCreate, ParticipantRead
from .models.tag import ConversationTagCreate, ConversationTagRead

router = APIRouter()


@router.post("")
async def conversation_create(
    payload: ConversationCreate, claims: TokenClaims = Depends(get_token_claims)
) -> ConversationRead:
    return await ConversationCreateControl(claims).conversation_create(payload)


@router.get("")
async def conversation_list(
    tags: list[str] = Query(),
    exclude: list[str] = Query([]),
    cursor: str | None = Query(
        None, description="Cursor for pagination (ISO 8601 timestamp)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of results per page"),
    search: str | None = None,
    claims: TokenClaims = Depends(get_token_claims),
) -> ConversationListPaginated:
    return await ConversationListControl(claims).conversation_list(
        tags, exclude, cursor, limit, search
    )


@router.post("/counts")
async def conversation_counts(
    payload: ConversationCountsPayload, claims: TokenClaims = Depends(get_token_claims)
) -> dict[str, int]:
    return await ConversationCountsControl(claims).conversation_counts(payload)


@router.post("/search")
async def conversation_search(
    payload: ConversationSearchPayload,
    offset: int = 0,
    claims: TokenClaims = Depends(get_token_claims),
) -> list[ConversationRead]:
    return await ConversationSearchControl(claims).conversation_search(payload, offset)


@router.get("/{conversation_id}")
async def conversation_detail(
    conversation_id: UUID,
    cursor: str | None = Query(
        None, description="Opaque cursor for the next page of messages"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to include"),
    order: MessageSortOrder = Query(
        "asc",
        description="Message sort order: asc for oldest-first, desc for newest-first",
    ),
    claims: TokenClaims = Depends(get_token_claims),
) -> ConversationRead:
    return await ConversationDetailControl(claims, conversation_id).conversation_detail(
        cursor, limit, order
    )


@router.post("/{conversation_id}/tags")
async def tag_create(
    conversation_id: UUID,
    payload: ConversationTagCreate,
    claims: TokenClaims = Depends(get_token_claims),
) -> ConversationTagRead:
    return await TagCreateControl(claims, conversation_id).tag_create(payload)


@router.post("/{conversation_id}/participants")
async def participant_create(
    conversation_id: UUID,
    payload: ParticipantCreate,
    claims: TokenClaims = Depends(get_token_claims),
) -> ParticipantRead:
    return await ParticipantCreateControl(claims, conversation_id).participant_create(
        payload
    )


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
    cursor: str | None = Query(
        None, description="Opaque cursor for the next page of messages"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of messages per page"),
    order: MessageSortOrder = Query(
        "asc",
        description="Message sort order: asc for oldest-first, desc for newest-first",
    ),
    claims: TokenClaims = Depends(get_token_claims),
) -> MessageListPaginated:
    return await MessageListControl(claims, conversation_id).message_list(
        cursor, limit, order
    )


@router.put("/{conversation_id}/messages/{message_id}")
async def message_update(
    conversation_id: UUID,
    message_id: UUID,
    payload: MessageUpdate,
    claims: TokenClaims = Depends(get_token_claims),
) -> MessageRead:
    controller = MessageUpdateControl(
        claims, conversation_id=conversation_id, message_id=message_id
    )
    return await controller.message_update(payload)
