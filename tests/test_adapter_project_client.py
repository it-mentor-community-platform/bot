from __future__ import annotations

import asyncio
from types import TracebackType
from typing import ClassVar, TypedDict, override

import httpx
import pytest

from src import adapter_client


class ProjectRequest(TypedDict):
    author_telegram_user_id: int
    author_telegram_username: str | None
    github_repository_url: str
    programming_language: str
    roadmap_project: str


class ProjectCall(TypedDict):
    url: str
    json: ProjectRequest


class FakeAsyncClient:
    response: ClassVar[httpx.Response] = httpx.Response(500)
    calls: ClassVar[list[ProjectCall]] = []
    init_auth: ClassVar[httpx.BasicAuth | None] = None
    init_timeout: ClassVar[float | None] = None

    def __init__(self, *, auth: httpx.BasicAuth, timeout: float) -> None:
        type(self).init_auth = auth
        type(self).init_timeout = timeout

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        return None

    async def post(self, url: str, *, json: ProjectRequest) -> httpx.Response:
        type(self).calls.append({"url": url, "json": json})
        return type(self).response


@pytest.fixture(autouse=True)
def fake_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeAsyncClient.calls = []
    FakeAsyncClient.init_auth = None
    FakeAsyncClient.init_timeout = None
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)


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
    assert FakeAsyncClient.init_timeout == 5.0
    assert isinstance(FakeAsyncClient.init_auth, httpx.BasicAuth)


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
        @override
        async def post(self, url: str, *, json: ProjectRequest) -> httpx.Response:
            _ = json
            request = httpx.Request("POST", url)
            raise httpx.RequestError("network", request=request)

    monkeypatch.setattr(httpx, "AsyncClient", RequestErrorClient)

    with pytest.raises(adapter_client.ProjectBackendUnavailableError):
        create_project()
