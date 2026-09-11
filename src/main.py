import asyncio
import logging

import uvicorn
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.config import logs
from src.config.env import TELEGRAM_BOT_TOKEN, METRICS_PORT
from src.custom_filters import EDITED_MESSAGE, MESSAGE_REACTION
from src.handler.add_project_handler import ADD_PROJECT_COMMAND_NAME, add_project
from src.handler.ai_handler import (
    AI_COMMAND,
    ask_ai,
)
from src.handler.error_handler import error_handler
from src.handler.interview_questions_list_handler import (
    INTERVIEW_QUESTIONS_LIST_COMMAND,
    list_interview_questions_messages,
)
from src.handler.projects_monthly_summary_handler import (
    PROJECTS_MONTHLY_SUMMARY_COMMAND_NAME,
    projects_monthly_summary,
)
from src.handler.reviews_monthly_summary_handler import (
    REVIEWS_MONTHLY_SUMMARY_COMMAND_NAME,
    reviews_monthly_summary,
)
from src.handler.run_tests_handler import RUN_TESTS_COMMAND_NAME, run_tests
from src.handler.search_interviews_with_question_handler import (
    SEARCH_INTERVIEWS_WITH_QUESTION_COMMAND_REGEXP,
    search_interviews_with_question,
)

from src.handler.update_finished_projects_handler import (
    UPDATE_FINISHED_PROJECTS_COMMAND,
    update_finished_projects,
)
from src.handler.update_interview_questions_popularity_handler import (
    UPDATE_INTERVIEW_QUESTIONS_POPULARITY,
    update_questions_popularity,
)
from src.metrics.telegram_instrumentation import instrument_application
from src.metrics.metrics_endpoint import metrics_app
from src.adapter_client import fetch_and_process_tasks

logs.configure()

log = logging.getLogger(__name__)


async def start_metrics_server() -> None:
    config: uvicorn.Config = uvicorn.Config(
        app=metrics_app, host="0.0.0.0", port=int(METRICS_PORT), log_level="info"
    )
    server: uvicorn.Server = uvicorn.Server(config)
    await server.serve()


async def start_bot() -> None:
    application = (
        ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).concurrent_updates(True).build()
    )
    instrument_application(application)

    add_project_handler = CommandHandler(ADD_PROJECT_COMMAND_NAME, add_project)
    search_interviews_with_question_handler = MessageHandler(
        filters.COMMAND
        & filters.Regex(SEARCH_INTERVIEWS_WITH_QUESTION_COMMAND_REGEXP)
        & ~EDITED_MESSAGE
        & ~MESSAGE_REACTION,
        search_interviews_with_question,
    )

    interview_questions_list_handler = CommandHandler(
        INTERVIEW_QUESTIONS_LIST_COMMAND, list_interview_questions_messages
    )
    update_interview_questions_popularity_handler = CommandHandler(
        UPDATE_INTERVIEW_QUESTIONS_POPULARITY,
        update_questions_popularity,
    )
    projects_monthly_summary_handler = CommandHandler(
        PROJECTS_MONTHLY_SUMMARY_COMMAND_NAME, projects_monthly_summary
    )
    reviews_monthly_summary_handler = CommandHandler(
        REVIEWS_MONTHLY_SUMMARY_COMMAND_NAME, reviews_monthly_summary
    )
    update_finished_projects_handler = CommandHandler(
        UPDATE_FINISHED_PROJECTS_COMMAND, update_finished_projects
    )
    ai_handler = CommandHandler(AI_COMMAND, ask_ai)
    run_tests_handler = CommandHandler(RUN_TESTS_COMMAND_NAME, run_tests)

    application.add_handler(add_project_handler)
    application.add_handler(search_interviews_with_question_handler)
    application.add_handler(interview_questions_list_handler)
    application.add_handler(update_interview_questions_popularity_handler)
    application.add_handler(projects_monthly_summary_handler)
    application.add_handler(reviews_monthly_summary_handler)
    application.add_handler(update_finished_projects_handler)
    application.add_handler(ai_handler)
    application.add_handler(run_tests_handler)
    application.add_error_handler(error_handler)

    async with application:
        await application.start()

        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        try:
            await asyncio.Event().wait()
        finally:
            await application.updater.stop()
            await application.stop()


async def start_adapter_polling() -> None:
    while True:
        try:
            await fetch_and_process_tasks()
        except Exception as e:
            log.error("Error in adapter polling loop: %s", e)

        await asyncio.sleep(10)


async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(start_bot())
        tg.create_task(start_metrics_server())
        tg.create_task(start_adapter_polling())


if __name__ == "__main__":
    asyncio.run(main())
