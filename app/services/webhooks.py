import hashlib
import hmac
from enum import Enum

import httpx
from asyncpg import Record

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

        try:
            await self._do_request(
                url=webhook_url, body=encoded_body, signature=signature
            )
        except Exception:
            logger.exception(
                "Unhandled webhook delivery failure: app_id=%s event=%s url=%s",
                self.app_id,
                event.value,
                webhook_url,
            )

    @staticmethod
    async def _do_request(
        *,
        url: str,
        body: bytes,
        signature: str,
    ) -> bool:
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
                if response.is_success:
                    return True

                logger.warning(
                    "Webhook endpoint rejected callback: url=%s status_code=%s response=%s",
                    url,
                    response.status_code,
                    response.text if response.text else "<empty>",
                )
                return False
            except httpx.RequestError as exc:
                logger.warning(
                    "Webhook request failed: url=%s error=%s",
                    url,
                    str(exc),
                )
                return False
            except Exception:
                logger.exception("Unexpected webhook client error: url=%s", url)
                return False
