from uuid import UUID

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.tag import (
    ConversationTagCreate,
    ConversationTagRead,
)


class TagCreateControl(BaseController):
    def __init__(self, claims: TokenClaims, conversation_id: UUID) -> None:
        super().__init__(claims)
        self.conversation_id = conversation_id

    async def tag_create(self, payload: ConversationTagCreate) -> ConversationTagRead:
        tags = await self._extract_tags()

        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.TAG)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

        query = (
            "INSERT INTO conversation_tags "
            "(conversation_id, tag_key, tag_value, tenant_id) "
            "VALUES ($1, $2, $3, $4) RETURNING *"
        )
        values = (
            self.conversation_id,
            payload.tag_key,
            payload.tag_value,
            self.tenant_id,
        )

        row: dict = await self.db.insert(
            query,
            values,
        )
        return ConversationTagRead(
            tag_key=row["tag_key"],
            tag_value=row["tag_value"],
            created_at=row["created_at"],
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
