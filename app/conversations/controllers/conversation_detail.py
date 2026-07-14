from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.conversation import ConversationRead
from app.conversations.models.message import MessageRead
from app.conversations.models.tag import ConversationTagRead


class ConversationDetailControl(BaseController):
    def __init__(self, claims: TokenClaims, conversation_id: UUID):
        super().__init__(claims)
        self.conversation_id = conversation_id

    @staticmethod
    async def _extract_tags(results: list[Record]) -> list[str]:
        return [f"{row["tag_key"]}:{row["tag_value"]}" for row in results]

    async def conversation_detail(
        self,
    ) -> ConversationRead:
        query = (
            "SELECT c.*, "
            "ct.tag_key, "
            "ct.tag_value, "
            "ct.created_at as tag_created_at, "
            "m.id as message_id, "
            "m.sender_id, "
            "m.sender_display_name, "
            "m.body, "
            "m.created_at as message_created_at, "
            "m.edited_at, "
            "m.deleted_at, "
            "m.reply_count "
            "FROM conversations c "
            "LEFT JOIN conversation_tags ct ON ct.conversation_id = c.id "
            "LEFT JOIN messages m ON m.conversation_id = c.id "
            "WHERE c.tenant_id = $1 AND c.id = $2"
        )

        results: list[Record] = await self.db.select_many(
            query,
            (
                self.tenant_id,
                self.conversation_id,
            ),
        )

        if not results:
            raise self.create_404("Not Found")

        tags: list[str] = await self._extract_tags(results)
        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Missing required scope for this conversation")

        base_row: Record = results[0]
        seen_tags: set[str] = set()
        seen_messages: set[UUID] = set()

        conversation = ConversationRead(
            id=base_row["id"],
            title=base_row["title"],
            created_by=base_row["created_by"],
            created_at=base_row["created_at"],
            archived_at=base_row["archived_at"],
        )
        for row in results:
            # Process tags (independently of messages)
            if row["tag_key"] is not None and row["tag_value"] is not None:
                tag_id = f"{row["tag_key"]}:{row["tag_value"]}"
                if tag_id not in seen_tags:
                    tag = ConversationTagRead(
                        tag_key=row["tag_key"],
                        tag_value=row["tag_value"],
                        created_at=row["tag_created_at"],
                    )
                    seen_tags.add(tag_id)
                    conversation.tags.append(tag)

            # Process messages (independently of tags)
            message_id = row["message_id"]
            if message_id is not None and message_id not in seen_messages:
                message = MessageRead(
                    id=message_id,
                    sender_display_name=row["sender_display_name"],
                    body=row["body"],
                    reply_count=row["reply_count"],
                    created_at=row["message_created_at"],
                    edited_at=row["edited_at"],
                    deleted_at=row["deleted_at"],
                )
                seen_messages.add(message_id)
                conversation.messages.append(message)
        return conversation
