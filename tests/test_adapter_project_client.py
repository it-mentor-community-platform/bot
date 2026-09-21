from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from src import adapter_client


class FakeAsyncClient:
    response: httpx.Response
    calls: list[dict[str, Any]] = []
    init_kwargs: list[dict[str, Any]] = []

    def __init__(self, **kwargs: Any) -> None:
        type(self).init_kwargs.append(kwargs)

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any]) -> httpx.Response:
        type(self).calls.append({"url": url, "json": json})
        return type(self).response


@pytest.fixture(autouse=True)
def fake_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeAsyncClient.calls = []
    FakeAsyncClient.init_kwargs = []
    monkeypatch.setattr(adapter_client.httpx, "AsyncClient", FakeAsyncClient)


def create_project() -> None:
    asyncio.run(
        adapter_client.create_project(
            author_telegram_user_id=123,
            author_telegram_username=None,
            github_repository_url="https://github.com/student/simulation",
            programming_language="Java",
            roadmap_project="simulation",
        )
    )


def test_create_project_uses_expected_request_and_basic_auth() -> None:
    FakeAsyncClient.response = httpx.Response(201)

    create_project()

    assert FakeAsyncClient.calls == [
        {
            "url": "http://backend.test/api/telegram-bot-adapter/projects",
            "json": {
                "author_telegram_user_id": 123,
                "author_telegram_username": None,
                "github_repository_url": "https://github.com/student/simulation",
                "programming_language": "Java",
                "roadmap_project": "simulation",
            },
        }
    ]
    assert FakeAsyncClient.init_kwargs[0]["timeout"] == 5.0
    assert isinstance(FakeAsyncClient.init_kwargs[0]["auth"], httpx.BasicAuth)


def test_create_project_accepts_created_response() -> None:
    FakeAsyncClient.response = httpx.Response(201)

    create_project()


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (400, adapter_client.InvalidProjectRequestError),
        (409, adapter_client.DuplicateProjectError),
        (500, adapter_client.ProjectBackendUnavailableError),
        (503, adapter_client.ProjectBackendUnavailableError),
    ],
)
def test_create_project_maps_backend_errors(
    status_code: int,
    expected_error: type[adapter_client.ProjectBackendError],
) -> None:
    FakeAsyncClient.response = httpx.Response(status_code)

    with pytest.raises(expected_error):
        create_project()


def test_create_project_maps_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class RequestErrorClient(FakeAsyncClient):
        async def post(self, url: str, json: dict[str, Any]) -> httpx.Response:
            request = httpx.Request("POST", url)
            raise httpx.RequestError("network", request=request)

    monkeypatch.setattr(adapter_client.httpx, "AsyncClient", RequestErrorClient)

    with pytest.raises(adapter_client.ProjectBackendUnavailableError):
        create_project()
