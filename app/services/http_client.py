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


class HttpClient:
    def __init__(
        self, base_url: str, headers: dict | None = None, timeout: float = 20.0
    ):
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout

    async def get(self, path: str) -> Any:
        return await self._do_request(method=HttpMethod.GET, path=path)

    async def post(
        self,
        path: str,
        data: dict | None = None,
        files: dict | None = None,
        json: dict | None = None,
    ) -> Any:
        return await self._do_request(
            method=HttpMethod.POST, path=path, data=data, files=files, json=json
        )

    async def patch(self, path: str, json: dict) -> Any:
        return await self._do_request(HttpMethod.PATCH, path=path, json=json)

    async def delete(self, path: str) -> int:
        return await self._do_request(HttpMethod.DELETE, path=path)

    async def _do_request(
        self,
        method: HttpMethod,
        path: str,
        data: dict | None = None,
        files: dict | None = None,
        json: dict | None = None,
    ) -> int | Any:
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout
        ) as client:
            try:
                url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
                response = await client.request(
                    method=method, url=url, json=json, data=data, files=files
                )
                response.raise_for_status()
                if method == HttpMethod.DELETE:
                    return response.status_code
                try:
                    return response.json()
                except ValueError:
                    return response.text if response.text else None

            except httpx.HTTPStatusError as e:
                # logger.error(
                #     f"Remote API error: {method} {url} - {e.response.status_code} - {e.response.text}"
                # )
                print(
                    f"Remote API error: {method} {url} - {e.response.status_code} - {e.response.text}"
                )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Remote API error: {e.response.text}",
                )
            except httpx.RequestError as e:
                print(f"Remote API request failed: {method} {url} - {str(e)}")
                # logger.error(f"Remote API request failed: {method} {url} - {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach remote service",
                )
            except Exception as e:
                print("Unexpected error in Http Client")
                # logger.error("Unexpected error in Http Client")
                raise HTTPException(status_code=500, detail="Internal server error")
