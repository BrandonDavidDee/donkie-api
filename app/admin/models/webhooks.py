from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class AppWebhookEvent(str, Enum):
    MESSAGE_CREATED = "message.created"
    PARTICIPANT_ADDED = "participant.added"


class AppWebhookBase(BaseModel):
    event_type: AppWebhookEvent
    url: str


class AppWebhookCreate(AppWebhookBase):
    pass


class AppWebhookRead(AppWebhookBase):
    id: UUID
    created_at: datetime
    revoked_at: datetime | None


class AppWebhookUpdate(AppWebhookBase):
    pass
