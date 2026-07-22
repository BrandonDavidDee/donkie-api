from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AppWebhookBase(BaseModel):
    event_type: str
    url: str


class AppWebhookCreate(AppWebhookBase):
    pass


class AppWebhookRead(AppWebhookBase):
    id: UUID
    created_at: datetime
    revoked_at: datetime | None


class AppWebhookUpdate(AppWebhookBase):
    pass
