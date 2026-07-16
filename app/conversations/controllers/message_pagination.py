import base64
import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from asyncpg import Record
from fastapi import HTTPException, status

from app.conversations.models.message import MessageListPaginated, MessageRead

MessageSortOrder = Literal["asc", "desc"]


class MessagePaginationMixin:
    @staticmethod
    def encode_message_cursor(
        created_at: datetime, message_id: UUID, order: MessageSortOrder
    ) -> str:
        payload = {
            "created_at": created_at.isoformat(),
            "id": str(message_id),
            "order": order,
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode(
            "utf-8"
        )

    @staticmethod
    def decode_message_cursor(
        cursor: str, expected_order: MessageSortOrder
    ) -> tuple[datetime, UUID]:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
            payload = json.loads(decoded)
            if payload["order"] != expected_order:
                raise ValueError("Cursor order does not match request order")
            return datetime.fromisoformat(payload["created_at"]), UUID(payload["id"])
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid cursor",
            ) from exc

    @staticmethod
    def message_cursor_operator(order: MessageSortOrder) -> str:
        return ">" if order == "asc" else "<"

    @staticmethod
    def message_order_clause(order: MessageSortOrder) -> str:
        direction = "ASC" if order == "asc" else "DESC"
        return f"created_at {direction}, id {direction}"

    @staticmethod
    def build_message_page(
        rows: list[Record], limit: int, order: MessageSortOrder
    ) -> MessageListPaginated:
        items: list[MessageRead] = []

        for row in rows[:limit]:
            items.append(
                MessageRead(
                    id=row["id"],
                    sender_display_name=row["sender_display_name"],
                    sender_id=row["sender_id"],
                    body=row["body"],
                    reply_count=row["reply_count"],
                    created_at=row["created_at"],
                    edited_at=row["edited_at"],
                    deleted_at=row["deleted_at"],
                )
            )

        has_more = len(rows) > limit
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            next_cursor = MessagePaginationMixin.encode_message_cursor(
                last_item.created_at, last_item.id, order
            )

        return MessageListPaginated(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )
