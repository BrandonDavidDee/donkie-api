from datetime import datetime
from pydantic import BaseModel


class ParticipantBase(BaseModel):
    user_id: str


class ParticipantCreate(ParticipantBase):
    joined_at: datetime


class ParticipantRead(ParticipantBase):
    last_read_at: datetime | None
    joined_at: datetime


class ParticipantUpdate(ParticipantBase):
    last_read_at: datetime
