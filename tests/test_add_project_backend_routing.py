from __future__ import annotations

import asyncio
import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from telegram.constants import ChatMemberStatus, ParseMode


@pytest.fixture
def handler(monkeypatch: pytest.MonkeyPatch):
    fake_repository = ModuleType("src.repository")
    fake_repository.find_reply_by_language_and_project = Mock(
        return_value="Project accepted"
    )
    monkeypatch.setitem(sys.modules, "src.repository", fake_repository)
    sys.modules.pop("src.handler.add_project_handler", None)

    module = importlib.import_module("src.handler.add_project_handler")
    monkeypatch.setattr(
        module,
        "parse_link",
        Mock(return_value="https://github.com/student/simulation"),
    )
    return module


def make_command(username: str | None = "student"):
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
    context_bot = SimpleNamespace(
        delete_message=AsyncMock(),
        forward_message=AsyncMock(),
        send_message=AsyncMock(),
        delete_messages=AsyncMock(),
    )
    context = SimpleNamespace(bot=context_bot)
    return update, context


def test_flag_false_keeps_legacy_google_sheets_path(
    handler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update, context = make_command()
    google_add_project = Mock()
    backend_create_project = AsyncMock()
    monkeypatch.setattr(handler.env, "ADD_PROJECT_VIA_COMMUNITY_BACKEND", False)
    monkeypatch.setattr(handler.env, "SEND_PROJECTS_TO_CHAT", False)
    monkeypatch.setattr(
        handler.google_sheet_service,
        "add_project",
        google_add_project,
    )
    monkeypatch.setattr(
        handler.adapter_client,
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
    handler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update, context = make_command(username=None)
    google_add_project = Mock()
    backend_create_project = AsyncMock()
    monkeypatch.setattr(handler.env, "ADD_PROJECT_VIA_COMMUNITY_BACKEND", True)
    monkeypatch.setattr(handler.env, "SEND_PROJECTS_TO_CHAT", False)
    monkeypatch.setattr(
        handler.google_sheet_service,
        "add_project",
        google_add_project,
    )
    monkeypatch.setattr(
        handler.adapter_client,
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
    context.bot.send_message.assert_awaited_once_with(
        chat_id=10,
        text="Project accepted",
        reply_to_message_id=20,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@pytest.mark.parametrize(
    ("error_name", "expected_message"),
    [
        ("DuplicateProjectError", "Этот проект уже добавлен"),
        (
            "InvalidProjectRequestError",
            "Не удалось добавить проект: проверьте ссылку, язык и название проекта",
        ),
        (
            "ProjectBackendUnavailableError",
            "Сервис проектов временно недоступен. Попробуйте позже",
        ),
    ],
)
def test_backend_failure_has_safe_friendly_reply(
    handler,
    monkeypatch: pytest.MonkeyPatch,
    error_name: str,
    expected_message: str,
) -> None:
    update, context = make_command()
    error_type = getattr(handler.adapter_client, error_name)
    backend_create_project = AsyncMock(side_effect=error_type())
    google_add_project = Mock()
    monkeypatch.setattr(handler.env, "ADD_PROJECT_VIA_COMMUNITY_BACKEND", True)
    monkeypatch.setattr(handler.env, "SEND_PROJECTS_TO_CHAT", False)
    monkeypatch.setattr(handler.asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(
        handler.google_sheet_service,
        "add_project",
        google_add_project,
    )
    monkeypatch.setattr(
        handler.adapter_client,
        "create_project",
        backend_create_project,
    )

    asyncio.run(handler.add_project(update, context))

    google_add_project.assert_not_called()
    context.bot.send_message.assert_awaited_once_with(
        chat_id=10,
        text=expected_message,
        reply_to_message_id=21,
    )
