from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController


class ConversationSearchControl(BaseController):
    def __init__(self, claims: TokenClaims):
        super().__init__(claims)

    async def conversation_search(
        self, tags: list[str], authorized_scope_tags: list[str], offset: int
    ):
        query = """
        SELECT DISTINCT c.*
        FROM conversations c
        JOIN conversation_tags ct ON ct.conversation_id = c.id
        WHERE ct.tenant_id = $1
          AND (ct.tag_key, ct.tag_value) IN ($2)
          AND EXISTS (
              SELECT 1 FROM conversation_tags ct2
              WHERE ct2.conversation_id = c.id
              AND (ct2.tag_key || ':' || ct2.tag_value) = ANY($3)
          )
        ORDER BY c.created_at
        LIMIT 20 OFFSET $4
        """

        results: list[Record] = await self.db.select_many(
            query,
            (
                self.tenant_id,
                tags,
                authorized_scope_tags,
                offset,
            ),
        )


