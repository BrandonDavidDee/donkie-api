from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AppKeyBase(BaseModel):
    pass


class AppKeyCreate(AppKeyBase):
    public_key: str


class AppKeyRead(AppKeyBase):
    id: UUID
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None


class AppKeyUpdate(AppKeyBase):
    public_key: str
