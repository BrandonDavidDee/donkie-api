import hashlib
import hmac
from enum import Enum
from typing import Any

import httpx
from asyncpg import Record
from fastapi import HTTPException, status

from app.authorization.claims import TokenUser
from app.logging_config import logger
from app.services.database import Database, db


class WebhookEvent(str, Enum):
    MESSAGE_CREATED = "message.created"
    PARTICIPANT_ADDED = "participant.added"


class WebhookService:
    def __init__(self, token_user: TokenUser):
        self.db: Database = db
        self.app_id = token_user.app_id
        self.webhook_secret = token_user.webhook_secret

    async def process_webhook(self, event: WebhookEvent, body: str) -> None:
        query = "SELECT url FROM app_webhooks WHERE app_id = $1 AND event_type = $2 AND revoked_at IS NULL"
        values = (
            self.app_id,
            event.value,
        )
        row: Record | None = await self.db.select_one(query, values)
        if row is None:
            return
        webhook_url = row["url"]

        encoded_body = body.encode()
        signature = hmac.new(
            self.webhook_secret.encode(), encoded_body, hashlib.sha256
        ).hexdigest()
        await self._do_request(url=webhook_url, body=encoded_body, signature=signature)

    @staticmethod
    async def _do_request(
        *,
        url: str,
        body: bytes,
        signature: str,
    ) -> int | Any:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.post(
                    url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Donkie-Signature": signature,
                    },
                )
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError:
                    return response.text if response.text else None

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Remote API error: {url} - {e.response.status_code} - {e.response.text}"
                )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Remote API error: {e.response.text}",
                )
            except httpx.RequestError as e:
                logger.error(f"Remote API request failed: {url} - {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach remote service",
                )
            except Exception as e:
                logger.error("Unexpected error in Http Client")
                raise HTTPException(status_code=500, detail="Internal server error")
