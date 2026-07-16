from datetime import datetime
from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.conversation import (
    ConversationListPaginated,
    ConversationRead,
)
from app.conversations.models.tag import ConversationTagRead


class ConversationListControl(BaseController):
    def __init__(self, claims: TokenClaims) -> None:
        super().__init__(claims)

    async def conversation_list(
        self,
        tags: list[str],
        exclude: list[str],
        cursor: str | None = None,
        limit: int = 50,
    ) -> ConversationListPaginated:
        # single call — the OR-loop happens inside has_permission_any
        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

        # Give em the clamps!
        limit = max(1, min(limit, 100))

        # Build query with cursor-based pagination
        # Query for limit+1 to determine if there are more results
        query = """
        SELECT c.*,
               ct.tag_key,
               ct.tag_value,
               ct.created_at as tag_created_at
        FROM conversations c
        JOIN conversation_tags ct ON ct.conversation_id = c.id
        WHERE ct.tenant_id = $1
          AND (ct.tag_key || ':' || ct.tag_value) = ANY($2)
          AND NOT EXISTS (
              SELECT 1 FROM conversation_tags ct2
              WHERE ct2.conversation_id = c.id
              AND ct2.tag_key = ANY($3)
          )
        """

        # Add cursor condition if provided
        params: list = [self.tenant_id, allowed_tags, exclude]
        if cursor:
            query += "  AND c.created_at < $4\n"
            params.append(cursor)

        query += """
        ORDER BY c.created_at DESC
        LIMIT ${}
        """.format(len(params) + 1)
        params.append(limit + 1)  # Fetch one extra to detect if there are more

        result: list[Record] = await self.db.select_many(query, tuple(params))
        output: dict[UUID, ConversationRead] = {}
        seen_tags: set[tuple[UUID, str]] = set()
        conversation_order: list[UUID] = []

        for row in result:
            conversation_id = row["id"]
            if conversation_id not in output:
                conv = ConversationRead(
                    id=conversation_id,
                    title=row["title"],
                    created_by=row["created_by"],
                    created_at=row["created_at"],
                    archived_at=row["archived_at"],
                )
                output[conversation_id] = conv
                conversation_order.append(conversation_id)

            if row["tag_key"] is not None and row["tag_value"] is not None:
                tag_id = f"{row['tag_key']}:{row['tag_value']}"
                tag_ref = (conversation_id, tag_id)
                if tag_ref not in seen_tags:
                    tag = ConversationTagRead(
                        tag_key=row["tag_key"],
                        tag_value=row["tag_value"],
                        created_at=row["tag_created_at"],
                    )
                    seen_tags.add(tag_ref)
                    output[conversation_id].tags.append(tag)

        # Determine if there are more results and extract the paginated set
        has_more = len(conversation_order) > limit
        paginated_ids = conversation_order[:limit]
        items = [output[conv_id] for conv_id in paginated_ids]

        # Set next_cursor to the created_at of the last item if there are more results
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            next_cursor = last_item.created_at.isoformat()

        return ConversationListPaginated(
            items=items, next_cursor=next_cursor, has_more=has_more
        )
