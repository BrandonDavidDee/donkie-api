import json
from uuid import UUID

from fastapi import BackgroundTasks

from app.authorization.claims import TokenUser
from app.base_controller import BaseController, PermissionAction
from app.conversations.models.message import (
    MessageCreate,
    MessageRead,
)
from app.services.webhooks import WebhookEvent, WebhookService


class MessageCreateControl(BaseController):
    def __init__(
        self, token_user: TokenUser, conversation_id: UUID, bg_tasks: BackgroundTasks
    ) -> None:
        super().__init__(token_user)
        self.bg_tasks = bg_tasks
        self.conversation_id = conversation_id
        self.webhooks = WebhookService(token_user)

    async def handle_webhook(self, payload: MessageCreate) -> None:
        body = json.dumps(payload, default=str)
        await self.webhooks.process_webhook(WebhookEvent.MESSAGE_CREATED, body)

    async def message_create(
        self,
        payload: MessageCreate,
    ) -> MessageRead:
        tags, participants = await self._extract_tags_and_participants()

        allowed_tags = [
            t for t in tags if self.has_permission_any([t], PermissionAction.WRITE)
        ]

        if not allowed_tags:
            raise self.create_403("Missing required scope for this conversation")

        sender_is_participant = self.user_id in participants
        if not sender_is_participant:
            await self._create_participant_from_sender()

        query = (
            "INSERT INTO messages "
            "(conversation_id, parent_message_id, tenant_id, sender_id, sender_display_name, body) "
            "VALUES ($1, $2, $3, $4, $5, $6) "
            "RETURNING *"
        )

        values = (
            self.conversation_id,
            None,
            self.tenant_id,
            self.user_id,
            self.display_name,
            payload.body,
        )
        row: dict = await self.db.insert(query, values)

        self.bg_tasks.add_task(self.handle_webhook, payload)

        return MessageRead(
            id=row["id"],
            sender_display_name=row["sender_display_name"],
            sender_id=row["sender_id"],
            body=row["body"],
            reply_count=row["reply_count"],
            created_at=row["created_at"],
            edited_at=row["edited_at"],
            deleted_at=row["deleted_at"],
        )

    async def _create_participant_from_sender(self) -> None:
        query = (
            "INSERT INTO participants "
            "(conversation_id, user_id, tenant_id) "
            "VALUES ($1, $2, $3) RETURNING *"
        )
        await self.db.insert(
            query,
            (
                self.conversation_id,
                self.user_id,
                self.tenant_id,
            ),
        )

    async def _extract_tags_and_participants(self) -> tuple[list[str], list[str]]:
        query = (
            "SELECT tag_key, tag_value, user_id "
            "FROM conversations c "
            "LEFT JOIN conversation_tags ct ON ct.conversation_id = c.id "
            "LEFT JOIN participants p ON p.conversation_id = c.id "
            "WHERE c.tenant_id = $1 AND c.id = $2"
        )

        results = await self.db.select_many(
            query,
            (
                self.tenant_id,
                self.conversation_id,
            ),
        )

        if not results:
            raise self.create_404("No Matching Conversation")

        tags: set[str] = set()
        participants: set[str] = set()
        for row in results:
            if row["tag_key"] and row["tag_value"]:
                tags.add(f"{row["tag_key"]}:{row["tag_value"]}")
            if row["user_id"]:
                participants.add(row["user_id"])

        return list(tags), list(participants)
