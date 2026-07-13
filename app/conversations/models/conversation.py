from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .message import MessageRead
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
    # participants: list[ParticipantRead] = Field(default_factory=list)


class ConversationUpdate(ConversationBase):
    pass
