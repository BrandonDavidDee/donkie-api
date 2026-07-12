from uuid import UUID

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.message import (
    MessageCreate,
    MessageRead,
)


class MessageCreateControl(BaseController):
    def __init__(self, claims: TokenClaims, conversation_id: UUID):
        super().__init__(claims)
        self.conversation_id = conversation_id

    async def message_create(
        self,
        payload: MessageCreate,
    ) -> MessageRead:
        tags: list[str] = await self._extract_tags()
        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.WRITE)
        ]

        if not allowed_tags:
            raise self.create_403("Missing required scope for this conversation")

        query = (
            "INSERT INTO messages "
            "(conversation_id, parent_message_id, tenant_id, sender_id, sender_display_name, body) "
            "VALUES ($1, $2, $3, $4, $5, $6) "
            "RETURNING *"
        )

        values = (
            self.conversation_id,
            None,
            self.tenant_id,
            self.user_id,
            payload.sender_display_name,
            payload.body,
        )
        row: dict = await self.db.insert(query, values)

        return MessageRead(
            id=row["id"],
            sender_display_name=row["sender_display_name"],
            body=row["body"],
            reply_count=row["reply_count"],
            created_at=row["created_at"],
            edited_at=row["edited_at"],
            deleted_at=row["deleted_at"],
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

        return [f"{row["tag_key"]}:{row["tag_value"]}" for row in results]
