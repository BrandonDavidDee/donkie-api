from uuid import UUID

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController
from app.conversations.models.participant import (
    ParticipantCreate,
    ParticipantRead,
)


class ParticipantCreateControl(BaseController):
    def __init__(self, claims: TokenClaims, conversation_id: UUID):
        super().__init__(claims)
        self.conversation_id = conversation_id

    async def participant_create(self, payload: ParticipantCreate) -> ParticipantRead:
        query = (
            "INSERT INTO participants "
            "(conversation_id, user_id, tenant_id) "
            "VALUES ($1, $2, $3) RETURNING *"
        )
        row: dict = await self.db.insert(
            query,
            (
                self.conversation_id,
                payload.user_id,
                self.tenant_id,
            ),
        )
        return ParticipantRead(
            user_id=row["user_id"],
            last_read_at=row["last_read_at"],
            joined_at=row["joined_at"],
        )
