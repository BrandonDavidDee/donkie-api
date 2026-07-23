from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.services.webhooks import WebhookEvent


class AppWebhookBase(BaseModel):
    event_type: WebhookEvent
    url: str


class AppWebhookCreate(AppWebhookBase):
    pass


class AppWebhookRead(AppWebhookBase):
    id: UUID
    created_at: datetime
    revoked_at: datetime | None


class AppWebhookUpdate(AppWebhookBase):
    pass
