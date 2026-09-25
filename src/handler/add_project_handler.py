import logging
import asyncio
import traceback
import sys

from telegram import ChatMember, Message, MessageEntity, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ContextTypes

from src.config import env
from src.config import constants
from src.google_sheet import google_sheet_service
from src import repository
from src.github import github_client

ADD_PROJECT_COMMAND_NAME = "addproject"

log = logging.getLogger(__name__)


async def add_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_member = update.effective_user
    command_message = update.effective_message

    assert (
        chat is not None
    ), "add_project command should be used in chat, it must not be None"
    assert (
        chat_member is not None
    ), "add_project command should be used by user, it must not be None"
    assert command_message is not None, "add_project command cannot be None"

    async def reply_with_error(text: str) -> None:
        error_message = await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_to_message_id=command_message.id,
        )
        await asyncio.sleep(10)
        _ = await context.bot.delete_messages(
            chat_id=chat.id,
            message_ids=[command_message.id, error_message.id],
        )
        return

    chat_member = await update.get_bot().get_chat_member(chat.id, chat_member.id)

    if not is_admin(chat_member) and not is_allowed_user(chat_member):
        log.error(
            f"{ADD_PROJECT_COMMAND_NAME} was called by not admin user: {chat_member.user.id}-{chat_member.status}"
        )
        await reply_with_error("У вас нет прав на использование данной команды")
        return

    if not is_reply(update.effective_message):
        log.error(f"{ADD_PROJECT_COMMAND_NAME} was called outside of reply")
        await reply_with_error("Сделайте реплай на сообщение со ссылкой на проект")
        return

    command_text = command_message.text

    assert command_text is not None, "Command text cannot be None"

    message_text = command_text[len("/" + ADD_PROJECT_COMMAND_NAME) :]

    if len(message_text.strip()) == 0:
        log.error(
            f"{ADD_PROJECT_COMMAND_NAME} was called with no arguments, expected 2"
        )
        await reply_with_error(
            f"Команда {ADD_PROJECT_COMMAND_NAME} должна вызываться с двумя параметрами - язык проекта и название проекта"
        )
        return

    args: list[str] = message_text.strip().split(" ")

    if len(args) != 2:
        log.error(
            f"{ADD_PROJECT_COMMAND_NAME} was called with {len(args)} arguments, expected 2"
        )
        await reply_with_error(
            f"Команда {ADD_PROJECT_COMMAND_NAME} должна вызываться с двумя параметрами - язык проекта и название проекта"
        )
        return

    language, project_name = args

    if project_name not in constants.PROJECT_NAMES:
        log.error(
            f"{ADD_PROJECT_COMMAND_NAME} was called with invalid project name '{project_name}' argument"
        )
        await reply_with_error("Неправильное название проекта (второй аргумент)")
        return

    student_message = command_message.reply_to_message

    assert (
        student_message is not None
    ), "Replied to message, i.e. student message with project link cannot be None"

    bot_reply_text = repository.find_reply_by_language_and_project(
        language, project_name
    )

    if bot_reply_text is None:
        log.error(
            f"{ADD_PROJECT_COMMAND_NAME} for project '{project_name}' and '{language}' didn't find suitable reply"
        )
        await reply_with_error("Сообщение по заданным критериям не найдено")
        return

    bot_reply_text = bot_reply_text.replace("\\n", "\n")

    projects_reviews_collection_chat_id = env.PROJECTS_REVIEWS_COLLECTION_CHAT_ID

    project_link = parse_link(student_message)

    if project_link is None:
        await reply_with_error("В сообщении нет ссылки на проект")
        return

    if github_client.is_github_repository_url(project_link):
        repository_available = await asyncio.to_thread(
            github_client.is_repository_available,
            project_link,
        )

        if repository_available is None:
            await reply_with_error(
                "Не удалось проверить доступность GitHub репозитория. Попробуйте позже."
            )
            return

        if not repository_available:
            log.warning("GitHub repository is not public: %s", project_link)
            _ = await context.bot.send_message(
                chat_id=chat.id,
                text="GitHub репозиторий недоступен по приложенной ссылке",
                reply_to_message_id=student_message.id,
            )
            _ = await context.bot.delete_message(
                chat_id=chat.id,
                message_id=command_message.id,
            )
            return

    try:
        google_sheet_service.add_project(project_name, language, project_link)

        _ = await context.bot.delete_message(
            chat_id=chat.id,
            message_id=command_message.id,
        )

        if env.SEND_PROJECTS_TO_CHAT:
            log.info(
                f"forwarding message because SEND_PROJECTS_TO_CHAT is {env.SEND_PROJECTS_TO_CHAT}"
            )
            _ = await context.bot.forward_message(
                from_chat_id=chat.id,
                chat_id=projects_reviews_collection_chat_id,
                message_id=student_message.id,
            )

        _ = await context.bot.send_message(
            chat_id=chat.id,
            text=bot_reply_text,
            reply_to_message_id=student_message.id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except Exception as e:
        file_name, line_number, func_name, _ = traceback.extract_tb(sys.exc_info()[2])[
            -1
        ]
        log.error(
            f"Error on {ADD_PROJECT_COMMAND_NAME} at {file_name}:{line_number} in {func_name}, message: {str(e)}"
        )
        await reply_with_error(str(e))
        return


def parse_link(message: Message) -> str | None:
    links_types = [MessageEntity.URL, MessageEntity.TEXT_LINK]

    message_entities: dict[MessageEntity, str]

    if message.caption is not None:
        message_entities = message.parse_caption_entities(links_types)
    else:
        message_entities = message.parse_entities(links_types)

    if len(message_entities) == 0:
        return None

    message_links: set[str] = set()

    for message_entity, value in message_entities.items():
        link = extract_link(message_entity, value)

        if link is None:
            continue

        message_links.add(normalize_link(link))

    if len(message_links) == 1:
        return message_links.pop()

    for link in message_links:
        if link.find("github.com") != -1:
            return link
        if link.find("gitlab.com") != -1:
            return link

    return None


def normalize_link(link: str) -> str:
    if link.startswith("http"):
        return link

    return "https://" + link


def extract_link(message_entity: MessageEntity, value: str) -> str | None:
    if message_entity.type is MessageEntity.TEXT_LINK:
        return message_entity.url

    return value


def is_admin(user: ChatMember) -> bool:
    return (
        user.status == ChatMemberStatus.ADMINISTRATOR
        or user.status == ChatMemberStatus.OWNER
    )


def is_allowed_user(user: ChatMember) -> bool:
    allowed_user_ids = env.ADD_PROJECT_ALLOWED_USER_IDS.split(",")
    allowed_user_ids = list(map(int, allowed_user_ids))

    user_id = user.user.id

    if user_id in allowed_user_ids:
        return True

    return False


def is_reply(message: Message | None) -> bool:
    if message is None:
        return False
    if message.reply_to_message is None:
        return False
    if message.reply_to_message.id == message.reply_to_message.message_thread_id:
        return False
    return True
