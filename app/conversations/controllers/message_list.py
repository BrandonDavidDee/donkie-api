from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController
from app.conversations.models.message import MessageRead


class MessageListControl(BaseController):
    def __init__(self, claims: TokenClaims, conversation_id: UUID):
        super().__init__(claims)
        self.conversation_id = conversation_id

    async def message_list(
        self,
    ) -> list[MessageRead]:
        # TODO: this can be condensed into one query, keep for now while testing
        tags = await self._extract_tags()

        for t in tags:
            if t not in self.scope:
                raise self.create_403(f"Scope does not permit tag '{t}'")

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
