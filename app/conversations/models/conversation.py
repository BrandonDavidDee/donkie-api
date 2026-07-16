from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .message import MessageListPaginated, MessageRead
from .participant import ParticipantRead
from .tag import ConversationTagCreate, ConversationTagRead


class ConversationBase(BaseModel):
    title: str | None


class ConversationCreate(ConversationBase):
    tags: list[ConversationTagCreate] = Field(default_factory=list)


class ConversationRead(ConversationBase):
    id: UUID
    created_by: str
    created_at: datetime
    archived_at: datetime | None
    tags: list[ConversationTagRead] = Field(default_factory=list)
    messages: list[MessageRead] = Field(default_factory=list)
    participants: list[ParticipantRead] = Field(default_factory=list)


class ConversationDetailRead(ConversationBase):
    id: UUID
    created_by: str
    created_at: datetime
    archived_at: datetime | None
    tags: list[ConversationTagRead] = Field(default_factory=list)
    participants: list[ParticipantRead] = Field(default_factory=list)
    messages: MessageListPaginated = Field(default_factory=MessageListPaginated)


class ConversationListPaginated(BaseModel):
    """Paginated response for conversation list."""

    items: list[ConversationRead] = Field(
        default_factory=list, description="List of conversations"
    )
    next_cursor: str | None = Field(
        None, description="Cursor for fetching next page; null if no more results"
    )
    has_more: bool = Field(
        False, description="Whether there are more results available"
    )


class ConversationUpdate(ConversationBase):
    pass
