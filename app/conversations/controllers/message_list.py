from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenUser
from app.base_controller import BaseController, PermissionAction
from app.conversations.controllers.message_pagination import (
    MessagePaginationMixin,
    MessageSortOrder,
)
from app.conversations.models.message import MessageListPaginated


class MessageListControl(BaseController, MessagePaginationMixin):
    def __init__(self, token_user: TokenUser, conversation_id: UUID) -> None:
        super().__init__(token_user)
        self.conversation_id = conversation_id

    async def message_list(
        self,
        cursor: str | None = None,
        limit: int = 50,
        order: MessageSortOrder = "asc",
        parent_message_id: UUID | None = None,
    ) -> MessageListPaginated:
        limit = max(1, min(limit, 100))
        tags = await self._extract_tags()

        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

        query = (
            "SELECT id, sender_display_name, sender_id, body, reply_count, created_at, edited_at, deleted_at "
            "FROM messages WHERE tenant_id = $1 AND conversation_id = $2"
        )

        values: list[object] = [
            self.tenant_id,
            self.conversation_id,
        ]

        # Filter by parent_message_id if provided; otherwise load top-level messages only
        if parent_message_id is not None:
            query += f" AND parent_message_id = ${len(values) + 1}"
            values.append(parent_message_id)
        else:
            query += f" AND parent_message_id IS NULL"

        if cursor:
            cursor_created_at, cursor_message_id = self.decode_message_cursor(
                cursor, order
            )
            query += f" AND (created_at, id) {self.message_cursor_operator(order)} (${len(values) + 1}, ${len(values) + 2})"
            values.extend([cursor_created_at, cursor_message_id])

        query += (
            f" ORDER BY {self.message_order_clause(order)} LIMIT ${len(values) + 1}"
        )
        values.append(limit + 1)

        results: list[Record] = await self.db.select_many(query, tuple(values))
        return self.build_message_page(results, limit, order)

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
