from datetime import datetime, timezone
from uuid import UUID

from app.authorization.claims import TokenUser
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.message import (
    MessageRead,
    MessageUpdate,
)


class MessageUpdateControl(BaseController):
    def __init__(
        self, token_user: TokenUser, *, conversation_id: UUID, message_id: UUID
    ) -> None:
        super().__init__(token_user)
        self.conversation_id = conversation_id
        self.message_id = message_id

    async def message_update(
        self,
        payload: MessageUpdate,
    ) -> MessageRead:
        if payload.sender_id != self.user_id:
            raise self.create_403("Cannot edit Someone Else's Message")

        tags = await self._extract_tags()

        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.WRITE)
        ]

        if not allowed_tags:
            raise self.create_403("Missing required scope for this conversation")

        query = (
            "UPDATE messages "
            "SET body = $1, "
            "edited_at = $2 "
            "WHERE tenant_id = $3 AND conversation_id = $4 AND id = $5 "
            "RETURNING *"
        )

        now = datetime.now(tz=timezone.utc)
        values = (
            payload.body,
            now,
            self.tenant_id,
            self.conversation_id,
            self.message_id,
        )
        row: dict = await self.db.insert(query, values)

        return MessageRead(
            id=row["id"],
            sender_display_name=row["sender_display_name"],
            sender_id=row["sender_id"],
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

        return [f"{row['tag_key']}:{row['tag_value']}" for row in results]
