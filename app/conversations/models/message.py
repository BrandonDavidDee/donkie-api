from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    body: str


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: UUID
    sender_display_name: str
    sender_id: str
    reply_count: int
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None


class MessageListPaginated(BaseModel):
    items: list[MessageRead] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


class MessageUpdate(MessageBase):
    reply_count: int
