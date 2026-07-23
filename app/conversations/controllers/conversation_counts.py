from asyncpg import Record
from pydantic import BaseModel

from app.authorization.claims import TokenUser
from app.base_controller import BaseController


class ConversationCountsPayload(BaseModel):
    tags: list[str]
    exclude: list[str] = []


class ConversationCountsControl(BaseController):
    def __init__(self, token_user: TokenUser) -> None:
        super().__init__(token_user)

    async def conversation_counts(
        self,
        payload: ConversationCountsPayload,
    ):
        query = """
        SELECT ct.tag_key || ':' || ct.tag_value AS tag, COUNT(DISTINCT c.id) AS count
        FROM conversations c
        JOIN conversation_tags ct ON ct.conversation_id = c.id
        WHERE ct.tenant_id = $1
          AND (ct.tag_key || ':' || ct.tag_value) = ANY($2)
          AND NOT EXISTS (
              SELECT 1 FROM conversation_tags ct2
              WHERE ct2.conversation_id = c.id
              AND ct2.tag_key = ANY($3)
          )
        GROUP BY ct.tag_key, ct.tag_value
        """

        results: list[Record] = await self.db.select_many(
            query,
            (
                self.tenant_id,
                payload.tags,
                payload.exclude,
            ),
        )
        output: dict[str, int] = {}
        for row in results:
            tag = row["tag"]
            count = row["count"]
            output[tag] = count

        return output
