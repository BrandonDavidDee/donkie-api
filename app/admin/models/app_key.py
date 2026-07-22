from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AppKeyBase(BaseModel):
    public_key: str


class AppKeyCreate(AppKeyBase):
    pass


class AppKeyRead(AppKeyBase):
    id: UUID
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None


class AppKeyUpdate(AppKeyBase):
    pass
