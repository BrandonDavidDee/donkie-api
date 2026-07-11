from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationTagBase(BaseModel):
    tag_key: str
    tag_value: str


class ConversationTagCreate(ConversationTagBase):
    pass


class ConversationTagRead(ConversationTagBase):
    created_at: datetime


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


class ConversationUpdate(ConversationBase):
    pass
