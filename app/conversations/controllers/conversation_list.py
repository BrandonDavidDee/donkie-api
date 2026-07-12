from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.conversation import ConversationRead


class ConversationListControl(BaseController):
    def __init__(self, claims: TokenClaims):
        super().__init__(claims)

    async def conversation_list(self, tags: list[str]) -> list[ConversationRead]:
        # single call — the OR-loop happens inside has_permission_any
        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.READ)
        ]

        if not allowed_tags:
            raise self.create_403("Not authorized to read any of the requested tags")

        query = """
        SELECT * FROM conversations c
        JOIN conversation_tags ct ON ct.conversation_id = c.id
        WHERE ct.tenant_id = $1 AND (ct.tag_key || ':' || ct.tag_value) = ANY($2)  
        """
        values = (self.tenant_id, tags)

        result: list[Record] = await self.db.select_many(query, values)
        output: list[ConversationRead] = []

        for row in result:
            conv = ConversationRead(
                id=row["id"],
                title=row["title"],
                created_by=row["created_by"],
                created_at=row["created_at"],
                archived_at=row["archived_at"],
            )
            output.append(conv)

        return output
