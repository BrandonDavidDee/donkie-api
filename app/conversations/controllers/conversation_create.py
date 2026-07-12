from app.authorization.claims import TokenClaims
from app.base_controller import BaseController
from app.conversations.models import (
    ConversationCreate,
    ConversationRead,
    ConversationTagRead,
)


class ConversationCreateControl(BaseController):
    def __init__(self, claims: TokenClaims):
        super().__init__(claims)

    async def conversation_create(
        self, payload: ConversationCreate
    ) -> ConversationRead:
        query = "INSERT INTO conversations (tenant_id, title, created_by) VALUES ($1, $2, $3) RETURNING *"
        row: dict = await self.db.insert(
            query,
            (
                self.tenant_id,
                payload.title,
                self.user_id,
            ),
        )
        conversation_id = row["id"]
        new_tags: list[ConversationTagRead] = []
        for tag in payload.tags:
            tag_query = (
                "INSERT INTO conversation_tags "
                "(conversation_id, tag_key, tag_value, tenant_id) "
                "VALUES ($1, $2, $3, $4) RETURNING *"
            )
            tag_values = (conversation_id, tag.tag_key, tag.tag_value, self.tenant_id)
            tag_row: dict = await self.db.insert(tag_query, tag_values)
            new_tag = ConversationTagRead(
                tag_key=tag_row["tag_key"],
                tag_value=tag_row["tag_value"],
                created_at=tag_row["created_at"],
            )
            new_tags.append(new_tag)

        return ConversationRead(
            id=conversation_id,
            title=row["title"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            archived_at=row["archived_at"],
            tags=new_tags,
        )
