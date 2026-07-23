import asyncio
from typing import cast
from uuid import uuid4

import httpx

from app.authorization.claims import TokenUser
from app.services.database import Database
from app.services.webhooks import WebhookEvent, WebhookService


class FakeAsyncClient:
    def __init__(self, response_or_error: httpx.Response | Exception, **_: object) -> None:
        self.response_or_error = response_or_error

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, *_: object, **__: object) -> httpx.Response:
        if isinstance(self.response_or_error, Exception):
            raise self.response_or_error
        return self.response_or_error


class FakeDatabase:
    def __init__(self, row: dict[str, str] | None) -> None:
        self.row = row

    async def select_one(self, query: str, values: tuple[object, ...]) -> dict[str, str] | None:
        return self.row


def create_token_user() -> TokenUser:
    return TokenUser(
        app_id=uuid4(),
        tenant_id="test-app:tenant-a",
        user_id="user-1",
        display_name="Test User",
        scope=["*:write"],
        webhook_secret="super-secret",
    )


def test_do_request_returns_true_for_success(monkeypatch) -> None:
    response = httpx.Response(
        status_code=202,
        request=httpx.Request("POST", "https://example.com/webhook"),
    )
    monkeypatch.setattr(
        "app.services.webhooks.httpx.AsyncClient",
        lambda **kwargs: FakeAsyncClient(response, **kwargs),
    )

    result = asyncio.run(
        WebhookService._do_request(
            url="https://example.com/webhook",
            body=b'{"hello":"world"}',
            signature="signature",
        )
    )

    assert result is True


def test_do_request_returns_false_for_rejected_callback(monkeypatch) -> None:
    response = httpx.Response(
        status_code=410,
        request=httpx.Request("POST", "https://example.com/webhook"),
        text="gone",
    )
    monkeypatch.setattr(
        "app.services.webhooks.httpx.AsyncClient",
        lambda **kwargs: FakeAsyncClient(response, **kwargs),
    )

    result = asyncio.run(
        WebhookService._do_request(
            url="https://example.com/webhook",
            body=b'{"hello":"world"}',
            signature="signature",
        )
    )

    assert result is False


def test_do_request_returns_false_for_unreachable_url(monkeypatch) -> None:
    error = httpx.ConnectError(
        "Name or service not known",
        request=httpx.Request("POST", "https://missing.example.com/webhook"),
    )
    monkeypatch.setattr(
        "app.services.webhooks.httpx.AsyncClient",
        lambda **kwargs: FakeAsyncClient(error, **kwargs),
    )

    result = asyncio.run(
        WebhookService._do_request(
            url="https://missing.example.com/webhook",
            body=b'{"hello":"world"}',
            signature="signature",
        )
    )

    assert result is False


def test_process_webhook_swallows_unexpected_delivery_errors(monkeypatch) -> None:
    service = WebhookService(create_token_user())
    service.db = cast(
        Database,
        cast(object, FakeDatabase({"url": "https://example.com/webhook"})),
    )

    async def explode(**_: object) -> bool:
        raise RuntimeError("boom")

    monkeypatch.setattr(WebhookService, "_do_request", staticmethod(explode))

    asyncio.run(service.process_webhook(WebhookEvent.MESSAGE_CREATED, '{"body":"hi"}'))



