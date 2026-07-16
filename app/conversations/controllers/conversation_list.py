from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.conversation import ConversationRead
from app.conversations.models.tag import ConversationTagRead


class ConversationListControl(BaseController):
    def __init__(self, claims: TokenClaims):
        super().__init__(claims)

    async def conversation_list(
        self, tags: list[str], exclude: list[str]
    ) -> list[ConversationRead]:
        # single call — the OR-loop happens inside has_permission_any
        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

        query = """
        SELECT *,
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
        ORDER BY c.created_at DESC
        """
        values = (self.tenant_id, allowed_tags, exclude)

        result: list[Record] = await self.db.select_many(query, values)
        output: dict[UUID, ConversationRead] = {}
        seen_tags: set[tuple[UUID, str]] = set()

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

        return [x for x in output.values()]
