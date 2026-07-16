from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.controllers.message_pagination import (
    MessagePaginationMixin,
    MessageSortOrder,
)
from app.conversations.models.conversation import ConversationRead
from app.conversations.models.participant import ParticipantRead
from app.conversations.models.tag import ConversationTagRead


class ConversationDetailControl(BaseController, MessagePaginationMixin):
    def __init__(self, claims: TokenClaims, conversation_id: UUID) -> None:
        super().__init__(claims)
        self.conversation_id = conversation_id

    @staticmethod
    async def _extract_tags(results: list[Record]) -> list[str]:
        return [f"{row['tag_key']}:{row['tag_value']}" for row in results]

    async def conversation_detail(
        self,
        cursor: str | None = None,
        limit: int = 50,
        order: MessageSortOrder = "asc",
    ) -> ConversationRead:
        limit = max(1, min(limit, 100))

        conversation_query = (
            "SELECT id, title, created_by, created_at, archived_at "
            "FROM conversations "
            "WHERE tenant_id = $1 AND id = $2"
        )
        base_row = await self.db.select_one(
            conversation_query, (self.tenant_id, self.conversation_id)
        )

        if not base_row:
            raise self.create_404("Not Found")

        tags_query = (
            "SELECT tag_key, tag_value, created_at as tag_created_at "
            "FROM conversation_tags "
            "WHERE tenant_id = $1 AND conversation_id = $2 "
            "ORDER BY created_at ASC, tag_key ASC, tag_value ASC"
        )
        tag_rows = await self.db.select_many(
            tags_query, (self.tenant_id, self.conversation_id)
        )

        tags: list[str] = await self._extract_tags(tag_rows)
        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Missing required scope for this conversation")

        participants_query = (
            "SELECT user_id, last_read_at, joined_at "
            "FROM participants "
            "WHERE tenant_id = $1 AND conversation_id = $2 "
            "ORDER BY joined_at ASC, user_id ASC"
        )
        participant_rows = await self.db.select_many(
            participants_query, (self.tenant_id, self.conversation_id)
        )

        message_query = (
            "SELECT id, sender_display_name, body, reply_count, created_at, edited_at, deleted_at "
            "FROM messages "
            "WHERE tenant_id = $1 AND conversation_id = $2"
        )
        message_values: list[object] = [self.tenant_id, self.conversation_id]
        if cursor:
            cursor_created_at, cursor_message_id = self.decode_message_cursor(
                cursor, order
            )
            message_query += f" AND (created_at, id) {self.message_cursor_operator(order)} (${len(message_values) + 1}, ${len(message_values) + 2})"
            message_values.extend([cursor_created_at, cursor_message_id])

        message_query += f" ORDER BY {self.message_order_clause(order)} LIMIT ${len(message_values) + 1}"
        message_values.append(limit + 1)
        message_rows = await self.db.select_many(message_query, tuple(message_values))

        conversation = ConversationRead(
            id=base_row["id"],
            title=base_row["title"],
            created_by=base_row["created_by"],
            created_at=base_row["created_at"],
            archived_at=base_row["archived_at"],
        )

        for row in tag_rows:
            conversation.tags.append(
                ConversationTagRead(
                    tag_key=row["tag_key"],
                    tag_value=row["tag_value"],
                    created_at=row["tag_created_at"],
                )
            )

        for row in participant_rows:
            conversation.participants.append(
                ParticipantRead(
                    user_id=row["user_id"],
                    last_read_at=row["last_read_at"],
                    joined_at=row["joined_at"],
                )
            )

        conversation.messages = self.build_message_page(message_rows, limit, order)
        return conversation
