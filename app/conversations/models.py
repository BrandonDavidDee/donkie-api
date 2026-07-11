from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConversationBase(BaseModel):
    title: str | None


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: UUID
    created_by: str
    created_at: datetime
    archived_at: datetime | None


class ConversationUpdate(ConversationBase):
    pass
