from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.message import MessageRead


class MessageListControl(BaseController):
    def __init__(self, claims: TokenClaims, conversation_id: UUID):
        super().__init__(claims)
        self.conversation_id = conversation_id

    async def message_list(
        self,
    ) -> list[MessageRead]:
        # TODO: Should this be be condensed into one query? If we add pagination, maybe it's cleaner to keep it separate?
        # if it stays separate the message list query can stay simple and straightforward.
        tags = await self._extract_tags()

        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

        query = "SELECT * FROM messages WHERE tenant_id = $1 AND conversation_id = $2"

        values = (
            self.tenant_id,
            self.conversation_id,
        )
        results: list[Record] = await self.db.select_many(query, values)
        output = []
        for row in results:
            message = MessageRead(
                id=row["id"],
                sender_display_name=row["sender_display_name"],
                body=row["body"],
                reply_count=row["reply_count"],
                created_at=row["created_at"],
                edited_at=row["edited_at"],
                deleted_at=row["deleted_at"],
            )
            output.append(message)

        return output

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
