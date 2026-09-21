import logging

import httpx

from src.config.env import (
    COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD,
    COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME,
    COMMUNITY_BACKEND_INTEGRATION_ROOT_URL,
)
from src.metrics.metric_definitions import telegram_tasks_processed_total

log = logging.getLogger(__name__)


class ProjectBackendError(Exception):
    pass


class DuplicateProjectError(ProjectBackendError):
    pass


class InvalidProjectRequestError(ProjectBackendError):
    pass


class ProjectBackendUnavailableError(ProjectBackendError):
    pass


async def create_project(
    author_telegram_user_id: int,
    author_telegram_username: str | None,
    github_repository_url: str,
    programming_language: str,
    roadmap_project: str,
) -> None:
    base_url = COMMUNITY_BACKEND_INTEGRATION_ROOT_URL.rstrip("/")
    url = f"{base_url}/api/telegram-bot-adapter/projects"
    auth = httpx.BasicAuth(
        COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME,
        COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD,
    )
    request = {
        "author_telegram_user_id": author_telegram_user_id,
        "author_telegram_username": author_telegram_username,
        "github_repository_url": github_repository_url,
        "programming_language": programming_language,
        "roadmap_project": roadmap_project,
    }

    try:
        async with httpx.AsyncClient(auth=auth, timeout=5.0) as client:
            response = await client.post(url, json=request)
    except httpx.RequestError as exc:
        log.error(
            "Project backend request failed for Telegram user id %s",
            author_telegram_user_id,
        )
        raise ProjectBackendUnavailableError from exc

    if response.status_code == 201:
        return
    if response.status_code == 400:
        raise InvalidProjectRequestError
    if response.status_code == 409:
        raise DuplicateProjectError
    if response.status_code >= 500:
        raise ProjectBackendUnavailableError

    log.error(
        "Unexpected project backend status %s for Telegram user id %s",
        response.status_code,
        author_telegram_user_id,
    )
    raise ProjectBackendError


async def fetch_and_process_tasks() -> None:

    base_url = COMMUNITY_BACKEND_INTEGRATION_ROOT_URL.rstrip("/")
    url = f"{base_url}/api/telegram-bot-adapter/tasks"
    params = {"count": 10}
    auth = httpx.BasicAuth(
        COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME,
        COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD,
    )

    try:
        async with httpx.AsyncClient(auth=auth, timeout=5.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            tasks = data.get("tasks")
            if not tasks:
                return

            for task in tasks:
                task_type = task.get("task_type", "unknown_type")
                log.info(f"Incoming task: '{task}'")
                payload = task.get("payload", {})
                await process_task(task_type, payload)
                telegram_tasks_processed_total.labels(task_type=task_type).inc()

    except httpx.HTTPStatusError as exc:
        try:
            error_msg = exc.response.json().get("message", "Unknown error")
        except Exception:
            error_msg = exc.response.text
        log.error(
            "Failed to process adapter task. Code: %s, Response: %s",
            exc.response.status_code,
            error_msg,
        )

    except httpx.RequestError as exc:
        log.error("Network error occurred while contacting adapter: %s", exc)

    except Exception as exc:
        exception_name = type(exc).__name__
        log.error(
            "Unexpected error occurred during task processing: %s", exception_name
        )


async def process_task(task_type=None, payload=None) -> None:
    log.info(f"Processing task '{task_type}' successfully parsed. Payload:\n{payload}")
    pass
