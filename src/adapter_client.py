import logging

import httpx

from src.config.env import BOT_ADAPTER_ENABLED, BOT_ADAPTER_URL, BOT_ADAPTER_USER, BOT_ADAPTER_PASSWORD

log = logging.getLogger(__name__)


async def fetch_and_process_tasks():
    if str(BOT_ADAPTER_ENABLED).lower() != "true":
        return

    if not BOT_ADAPTER_URL or not BOT_ADAPTER_USER or not BOT_ADAPTER_PASSWORD:
        log.error("Configuration error: BOT_ADAPTER_URL, USER, or PASSWORD is not set in .env")
        return

    base_url = BOT_ADAPTER_URL.rstrip('/')
    url = f"{base_url}/api/telegram-bot-adapter/tasks"
    params = {"count": count}
    auth = httpx.BasicAuth(BOT_ADAPTER_USER, BOT_ADAPTER_PASSWORD)

    try:
        async with httpx.AsyncClient(auth=auth, timeout=5.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            task_count = data.get("count", 0)
            tasks = data.get("tasks", [])

            if task_count == 0 or not tasks:
                return

            for task in tasks:
                task_type = task.get("task_type", "unknown_type")
                payload = task.get("payload", {})

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
