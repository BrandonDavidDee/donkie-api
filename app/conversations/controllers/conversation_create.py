from app.authorization.claims import TokenClaims
from app.base_controller import BaseController
from app.conversations.models.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationTagRead,
)
from app.conversations.models.message import MessageListPaginated
from app.conversations.models.participant import ParticipantRead


class ConversationCreateControl(BaseController):
    """
    Creating a conversation requires all included tags to be in the token scopes
    """

    def __init__(self, claims: TokenClaims) -> None:
        super().__init__(claims)

    async def conversation_create(
        self, payload: ConversationCreate
    ) -> ConversationRead:
        tags = [f"{tag.tag_key}:{tag.tag_value}" for tag in payload.tags]
        if not self.can_create_with_tags(tags):
            raise self.create_403(
                "Not authorized to create a conversation with these tags"
            )

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

        messages = MessageListPaginated(
            items=[],
            next_cursor=None,
            has_more=False,
        )
        participant = await self._create_participant_from_sender(conversation_id)

        return ConversationRead(
            id=conversation_id,
            title=row["title"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            archived_at=row["archived_at"],
            tags=new_tags,
            messages=messages,
            participants=[participant],
        )

    async def _create_participant_from_sender(
        self, conversation_id: int
    ) -> ParticipantRead:
        query = (
            "INSERT INTO participants "
            "(conversation_id, user_id, tenant_id) "
            "VALUES ($1, $2, $3) RETURNING *"
        )
        row: dict = await self.db.insert(
            query,
            (
                conversation_id,
                self.user_id,
                self.tenant_id,
            ),
        )
        return ParticipantRead(
            user_id=row["user_id"],
            last_read_at=row["last_read_at"],
            joined_at=row["joined_at"],
        )
