from uuid import UUID

from app.authorization.claims import TokenUser
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.participant import (
    ParticipantCreate,
    ParticipantRead,
)


class ParticipantCreateControl(BaseController):
    def __init__(self, token_user: TokenUser, conversation_id: UUID) -> None:
        super().__init__(token_user)
        self.conversation_id = conversation_id

    async def participant_create(self, payload: ParticipantCreate) -> ParticipantRead:
        tags = await self._extract_tags()

        allowed_tags = [
            t
            for t in tags
            if self.has_permission_any([t], PermissionAction.MANAGE_PARTICIPANTS)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

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

    async def _extract_tags(self) -> list[str]:
        tag_query = "SELECT * FROM conversation_tags WHERE tenant_id = $1 AND conversation_id = $2"
        results = await self.db.select_many(
            tag_query,
            (
                self.tenant_id,
                self.conversation_id,
            ),
        )

        if not results:
            raise self.create_404("No Matching Conversation")

        return [f"{row['tag_key']}:{row['tag_value']}" for row in results]
