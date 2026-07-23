import hashlib
import hmac
from enum import Enum
from typing import Any

import httpx
from fastapi import HTTPException, status

# from app.logging_config import logger


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"


class WebhookService:
    async def process_webhook(self, webhook_url: str, body: bytes, webhook_secret: str):
        signature = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        return await self._do_request(url=webhook_url, body=body, signature=signature)

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
                # logger.error(
                #     f"Remote API error: {method} {url} - {e.response.status_code} - {e.response.text}"
                # )
                print(
                    f"Remote API error: {url} - {e.response.status_code} - {e.response.text}"
                )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Remote API error: {e.response.text}",
                )
            except httpx.RequestError as e:
                print(f"Remote API request failed: {url} - {str(e)}")
                # logger.error(f"Remote API request failed: {method} {url} - {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach remote service",
                )
            except Exception as e:
                print("Unexpected error in Http Client")
                # logger.error("Unexpected error in Http Client")
                raise HTTPException(status_code=500, detail="Internal server error")
