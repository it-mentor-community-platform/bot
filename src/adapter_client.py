import logging

import httpx

from src.config.env import COMMUNITY_BACKEND_INTEGRATION_ENABLED, COMMUNITY_BACKEND_INTEGRATION_ROOT_URL, \
    COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME, COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD
from src.metrics.metric_definitions import telegram_tasks_processed_total

log = logging.getLogger(__name__)


async def fetch_and_process_tasks():
    if str(COMMUNITY_BACKEND_INTEGRATION_ENABLED).lower() != "true":
        return

    if not COMMUNITY_BACKEND_INTEGRATION_ROOT_URL or not COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME or not COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD:
        log.error("Configuration error: COMMUNITY_BACKEND_INTEGRATION_ROOT_URL, USER, or PASSWORD is not set in .env")
        return

    base_url = COMMUNITY_BACKEND_INTEGRATION_ROOT_URL.rstrip('/')
    url = f"{base_url}/api/telegram-bot-adapter/tasks"
    params = {"count": 10}
    auth = httpx.BasicAuth(COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME,
                           COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD)

    try:
        async with httpx.AsyncClient(auth=auth, timeout=5.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            tasks = data.get("tasks", [])

            if not tasks:
                return

            for task in tasks:
                task_type = task.get("task_type", "unknown_type")
                payload = task.get("payload", {})
                await process_task(task_type, payload)
                telegram_tasks_processed_total.labels(task_type=task_type).inc()

                log.info(f"Received task from adapter [type: {task_type}]: {payload}")

    except httpx.HTTPStatusError as exc:
        try:
            error_msg = exc.response.json().get("message", "Unknown error")
        except Exception:
            error_msg = exc.response.text
        log.error("Failed to process adapter task. Code: %s, Response: %s", exc.response.status_code, error_msg)

    except httpx.RequestError as exc:
        log.error("Network error occurred while contacting adapter: %s", exc)

    except Exception as exc:
        exception_name = type(exc).__name__
        log.error("Unexpected error occurred during task processing: %s", exception_name)


async def process_task(task_type=None, payload=None):
    pass
