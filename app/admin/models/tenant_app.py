from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.admin.models.app_key import AppKeyRead
from app.admin.models.webhooks import AppWebhookRead


class AppBase(BaseModel):
    name: str


class AppCreate(AppBase):
    pass


class AppRead(AppBase):
    id: UUID
    created_at: datetime
    revoked_at: datetime | None
    keys: list[AppKeyRead] = Field(default_factory=list)
    webhooks: list[AppWebhookRead] = Field(default_factory=list)


class AppReadOnCreate(AppRead):
    webhook_secret: str


class AppUpdate(AppBase):
    pass
