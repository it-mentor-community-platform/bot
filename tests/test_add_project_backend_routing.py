from __future__ import annotations

import asyncio
import importlib
import sys
from collections.abc import Callable, Coroutine
from types import ModuleType, SimpleNamespace
from typing import Protocol, cast
from unittest.mock import AsyncMock, Mock

import pytest
from telegram.constants import ChatMemberStatus, ParseMode

from src import adapter_client
from src.config import env
from src.google_sheet import google_sheet_service


class FakeRepositoryModule(ModuleType):
    find_reply_by_language_and_project: Callable[[str, str], str]

    def __init__(self) -> None:
        super().__init__("src.repository")
        self.find_reply_by_language_and_project = self._find_reply

    @staticmethod
    def _find_reply(_language: str, _project_name: str) -> str:
        return "Project accepted"


class HandlerModule(Protocol):
    parse_link: Callable[[object], str | None]
    add_project: Callable[
        [object, object],
        Coroutine[object, object, None],
    ]


@pytest.fixture
def handler(monkeypatch: pytest.MonkeyPatch) -> HandlerModule:
    fake_repository = FakeRepositoryModule()
    monkeypatch.setitem(sys.modules, "src.repository", fake_repository)
    _ = sys.modules.pop("src.handler.add_project_handler", None)

    imported_module = importlib.import_module("src.handler.add_project_handler")
    module = cast(HandlerModule, cast(object, imported_module))

    def fake_parse_link(_message: object) -> str:
        return "https://github.com/student/simulation"

    monkeypatch.setattr(
        module,
        "parse_link",
        fake_parse_link,
    )
    return module


def make_command(
    username: str | None = "student",
) -> tuple[SimpleNamespace, SimpleNamespace, AsyncMock]:
    student = SimpleNamespace(id=123, username=username)
    student_message = SimpleNamespace(
        id=20,
        from_user=student,
        message_thread_id=None,
    )
    command_message = SimpleNamespace(
        id=21,
        text="/addproject Java simulation",
        reply_to_message=student_message,
    )
    admin_user = SimpleNamespace(id=100)
    admin_member = SimpleNamespace(
        user=admin_user,
        status=ChatMemberStatus.ADMINISTRATOR,
    )
    telegram_bot = SimpleNamespace(get_chat_member=AsyncMock(return_value=admin_member))
    update = SimpleNamespace(
        effective_chat=SimpleNamespace(id=10),
        effective_user=admin_user,
        effective_message=command_message,
        get_bot=Mock(return_value=telegram_bot),
    )
    send_message = AsyncMock()
    context_bot = SimpleNamespace(
        delete_message=AsyncMock(),
        forward_message=AsyncMock(),
        send_message=send_message,
        delete_messages=AsyncMock(),
    )
    context = SimpleNamespace(bot=context_bot)
    return update, context, send_message


def test_flag_false_keeps_legacy_google_sheets_path(
    handler: HandlerModule,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update, context, _send_message = make_command()
    google_add_project = Mock()
    backend_create_project = AsyncMock()
    monkeypatch.setattr(env, "ADD_PROJECT_VIA_COMMUNITY_BACKEND", False)
    monkeypatch.setattr(env, "SEND_PROJECTS_TO_CHAT", False)
    monkeypatch.setattr(
        google_sheet_service,
        "add_project",
        google_add_project,
    )
    monkeypatch.setattr(
        adapter_client,
        "create_project",
        backend_create_project,
    )

    asyncio.run(handler.add_project(update, context))

    google_add_project.assert_called_once_with(
        "simulation",
        "Java",
        "https://github.com/student/simulation",
    )
    backend_create_project.assert_not_awaited()


def test_flag_true_uses_backend_only_and_keeps_success_reply(
    handler: HandlerModule,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update, context, send_message = make_command(username=None)
    google_add_project = Mock()
    backend_create_project = AsyncMock()
    monkeypatch.setattr(env, "ADD_PROJECT_VIA_COMMUNITY_BACKEND", True)
    monkeypatch.setattr(env, "SEND_PROJECTS_TO_CHAT", False)
    monkeypatch.setattr(
        google_sheet_service,
        "add_project",
        google_add_project,
    )
    monkeypatch.setattr(
        adapter_client,
        "create_project",
        backend_create_project,
    )

    asyncio.run(handler.add_project(update, context))

    backend_create_project.assert_awaited_once_with(
        author_telegram_user_id=123,
        author_telegram_username=None,
        github_repository_url="https://github.com/student/simulation",
        programming_language="Java",
        roadmap_project="simulation",
    )
    google_add_project.assert_not_called()
    send_message.assert_awaited_once_with(
        chat_id=10,
        text="Project accepted",
        reply_to_message_id=20,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@pytest.mark.parametrize(
    ("error_type", "expected_message"),
    [
        (adapter_client.DuplicateProjectError, "Этот проект уже добавлен"),
        (
            adapter_client.InvalidProjectRequestError,
            "Не удалось добавить проект: проверьте ссылку, язык и название проекта",
        ),
        (
            adapter_client.ProjectBackendUnavailableError,
            "Сервис проектов временно недоступен. Попробуйте позже",
        ),
    ],
)
def test_backend_failure_has_safe_friendly_reply(
    handler: HandlerModule,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[adapter_client.ProjectBackendError],
    expected_message: str,
) -> None:
    update, context, send_message = make_command()
    backend_create_project = AsyncMock(side_effect=error_type())
    google_add_project = Mock()
    monkeypatch.setattr(env, "ADD_PROJECT_VIA_COMMUNITY_BACKEND", True)
    monkeypatch.setattr(env, "SEND_PROJECTS_TO_CHAT", False)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(
        google_sheet_service,
        "add_project",
        google_add_project,
    )
    monkeypatch.setattr(
        adapter_client,
        "create_project",
        backend_create_project,
    )

    asyncio.run(handler.add_project(update, context))

    google_add_project.assert_not_called()
    send_message.assert_awaited_once_with(
        chat_id=10,
        text=expected_message,
        reply_to_message_id=21,
    )
