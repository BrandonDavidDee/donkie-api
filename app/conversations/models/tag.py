from datetime import datetime

from pydantic import BaseModel


class ConversationTagBase(BaseModel):
    tag_key: str
    tag_value: str


class ConversationTagCreate(ConversationTagBase):
    pass


class ConversationTagRead(ConversationTagBase):
    created_at: datetime
