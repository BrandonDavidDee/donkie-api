from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.authorization.claims import TokenUser, get_token_user

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
    payload: ConversationCreate,
    token_user: TokenUser = Depends(get_token_user),
) -> ConversationRead:
    return await ConversationCreateControl(token_user).conversation_create(payload)


@router.get("")
async def conversation_list(
    tags: list[str] = Query(),
    exclude: list[str] = Query([]),
    cursor: str | None = Query(
        None, description="Cursor for pagination (ISO 8601 timestamp)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of results per page"),
    search: str | None = None,
    token_user: TokenUser = Depends(get_token_user),
) -> ConversationListPaginated:
    return await ConversationListControl(token_user).conversation_list(
        tags, exclude, cursor, limit, search
    )


@router.post("/counts")
async def conversation_counts(
    payload: ConversationCountsPayload,
    token_user: TokenUser = Depends(get_token_user),
) -> dict[str, int]:
    return await ConversationCountsControl(token_user).conversation_counts(payload)


@router.post("/search")
async def conversation_search(
    payload: ConversationSearchPayload,
    offset: int = 0,
    token_user: TokenUser = Depends(get_token_user),
) -> list[ConversationRead]:
    return await ConversationSearchControl(token_user).conversation_search(
        payload, offset
    )


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
    token_user: TokenUser = Depends(get_token_user),
) -> ConversationRead:
    return await ConversationDetailControl(
        token_user, conversation_id
    ).conversation_detail(cursor, limit, order)


@router.post("/{conversation_id}/tags")
async def tag_create(
    conversation_id: UUID,
    payload: ConversationTagCreate,
    token_user: TokenUser = Depends(get_token_user),
) -> ConversationTagRead:
    return await TagCreateControl(token_user, conversation_id).tag_create(payload)


@router.post("/{conversation_id}/participants")
async def participant_create(
    conversation_id: UUID,
    payload: ParticipantCreate,
    token_user: TokenUser = Depends(get_token_user),
) -> ParticipantRead:
    return await ParticipantCreateControl(
        token_user, conversation_id
    ).participant_create(payload)


@router.post("/{conversation_id}/messages")
async def message_create(
    conversation_id: UUID,
    payload: MessageCreate,
    token_user: TokenUser = Depends(get_token_user),
) -> MessageRead:
    return await MessageCreateControl(token_user, conversation_id).message_create(
        payload
    )


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
    parent_message_id: UUID | None = Query(
        None,
        description="Optional parent message ID to load replies; if not provided, loads top-level messages",
    ),
    token_user: TokenUser = Depends(get_token_user),
) -> MessageListPaginated:
    return await MessageListControl(token_user, conversation_id).message_list(
        cursor, limit, order, parent_message_id
    )


@router.put("/{conversation_id}/messages/{message_id}")
async def message_update(
    conversation_id: UUID,
    message_id: UUID,
    payload: MessageUpdate,
    token_user: TokenUser = Depends(get_token_user),
) -> MessageRead:
    controller = MessageUpdateControl(
        token_user, conversation_id=conversation_id, message_id=message_id
    )
    return await controller.message_update(payload)
