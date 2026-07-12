from uuid import UUID

from asyncpg import Record

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController


class ConversationDetail(BaseController):
    def __init__(self, claims: TokenClaims):
        super().__init__(claims)

    async def get_conversations(self, tags: list[str]):
        for t in tags:
            if t not in self.scope:
                raise self.create_403(f"Scope does not permit tag '{t}'")

        query = """
        SELECT * FROM conversations c
        JOIN conversation_tags ct ON ct.conversation_id = c.id
        WHERE ct.tenant_id = $1 AND (ct.tag_key || ':' || ct.tag_value) = ANY($2)  
        """
        values = (self.tenant_id, tags)
        result: list[Record] = await self.db.select_many(query, values)
        output: list[UUID] = []
        for row in result:
            output.append(row["id"])
        return {
            "tags": tags,
            "output": output,
        }
