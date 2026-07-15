from asyncpg import Record
from pydantic import BaseModel

from app.authorization.claims import TokenClaims
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.conversation import ConversationRead


class SearchPair(BaseModel):
    tag_key: str
    value_search: str


class ConversationSearchPayload(BaseModel):
    search_pairs: list[SearchPair]


class ConversationSearchControl(BaseController):
    def __init__(self, claims: TokenClaims):
        super().__init__(claims)

    @staticmethod
    def _escape_ilike(value: str) -> str:
        escaped = value.replace("\\", "\\\\")
        escaped = escaped.replace("%", "\\%")
        escaped = escaped.replace("_", "\\_")
        return f"%{escaped}%"

    def _allowed_read_tags(self) -> tuple[bool, list[str]]:
        wildcard_scope = f"*:{PermissionAction.READ.value}"
        if wildcard_scope in self.scope:
            return True, []

        read_suffix = f":{PermissionAction.READ.value}"
        allowed_tags = [
            scope[: -len(read_suffix)]
            for scope in self.scope
            if scope.endswith(read_suffix) and scope != wildcard_scope
        ]
        return False, allowed_tags

    async def conversation_search(
        self, payload: ConversationSearchPayload, offset: int
    ) -> list[ConversationRead]:
        if not payload.search_pairs:
            return []

        has_wildcard_read, allowed_read_tags = self._allowed_read_tags()
        if not has_wildcard_read and not allowed_read_tags:
            raise self.create_403("Not authorized to read conversations")

        search_tag_keys = [pair.tag_key for pair in payload.search_pairs]
        search_patterns = [
            self._escape_ilike(pair.value_search) for pair in payload.search_pairs
        ]

        query = """
        SELECT DISTINCT c.*
        FROM conversations c
        WHERE c.tenant_id = $1
          AND EXISTS (
              SELECT 1
              FROM conversation_tags ct
              JOIN UNNEST($2::text[], $3::text[]) AS sp(tag_key, value_pattern)
                ON ct.tag_key = sp.tag_key
              WHERE ct.conversation_id = c.id
                AND ct.tenant_id = $1
                AND ct.tag_value ILIKE sp.value_pattern ESCAPE '\\'
          )
          AND (
              $4::boolean
              OR EXISTS (
              SELECT 1 FROM conversation_tags ct2
              WHERE ct2.conversation_id = c.id
                AND ct2.tenant_id = $1
                AND (ct2.tag_key || ':' || ct2.tag_value) = ANY($5::text[])
              )
          )
        ORDER BY c.created_at
        LIMIT 20 OFFSET $6
        """

        results: list[Record] = await self.db.select_many(
            query,
            (
                self.tenant_id,
                search_tag_keys,
                search_patterns,
                has_wildcard_read,
                allowed_read_tags,
                offset,
            ),
        )

        return [
            ConversationRead(
                id=row["id"],
                title=row["title"],
                created_by=row["created_by"],
                created_at=row["created_at"],
                archived_at=row["archived_at"],
            )
            for row in results
        ]
