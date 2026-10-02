import asyncio
import logging
import random

from telegram import ChatMember, Message, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ContextTypes

from src.config import env
from src.handler import util
from src.mcp import client as mcp_client

AI_COMMAND = "ai"
SEARCH_COMMAND = "search"

log = logging.getLogger(__name__)

stickers = [
    "CAACAgIAAyEFAASGWTCcAAIDaWmhnTUvJKFOTb0ebYgeAAGn2TNkWQACVTMAApF94EopG64GrXuhyjoE",
    "CAACAgIAAyEFAASGWTCcAAIDammhnTYWdj_rjvC0nscSgOzBOijGAAL5LgACRufgSo_Jf46d83V2OgQ",
    "CAACAgIAAyEFAASGWTCcAAIDZGmhmhh-ICxO0dDfQuaAaVIKysR9AAJrLgACVDzgSpPG1z72JoVROgQ",
    "CAACAgIAAyEFAASGWTCcAAIDbGmhnTnePJblJ1UEDlmjDRphzGv4AAKdeAAC-xjhSmGuWzP8XNNCOgQ",
    "CAACAgIAAyEFAASGWTCcAAIDZWmhmhyGYO1BFtYWK2NUBp6QFcYAAwMnAAKXC_lKLnyN8goo3V06BA",
    "CAACAgIAAyEFAASGWTCcAAIDZmmhmia-zPwUGNzXaRfgfKuj6k9gAAJiQwAC_LkBSCzXlvIp2lFUOgQ",
]


async def ask_ai(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command_name: str = AI_COMMAND,
):
    chat = update.effective_chat
    chat_member = update.effective_user
    command_message = update.effective_message

    assert chat is not None, "Chat in which command is called cannot be None"
    assert (
        chat_member is not None
    ), f"{command_name} command should be used by user, it must not be None"
    assert command_message is not None, "Message that triggered bot cannot be None"

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

    tool_set = get_tool_set_for_chat(chat.id, command_name)

    if tool_set is None:
        log.error(
            f"{command_name} was called outside of allowed chats, in chat: {chat.effective_name}"
        )
        await reply_with_error("Команда запрещена в этом чате")
        return

    chat_member = await update.get_bot().get_chat_member(chat.id, chat_member.id)

    command_text = command_message.text

    assert command_text is not None, "Command text cannot be None"

    if command_name == SEARCH_COMMAND:
        message_text = " ".join(context.args)
    else:
        message_text = command_text[len("/" + command_name) :]

    if len(message_text.strip()) == 0:
        log.error(f"{command_name} was called with no argument, expected 1")
        await reply_with_error(f"Команда {command_name} должна вызываться с запросом")
        return

    sent_message: Message | None = None
    messages: list[str] = []

    if env.AI_COMMAND_STICKER_REPLY == True:
        sent_sticker = await context.bot.send_sticker(
            chat_id=chat.id,
            sticker=random.choice(stickers),
            message_thread_id=command_message.message_thread_id,
            reply_to_message_id=command_message.id,
        )
        messages = []
        for llm_response in mcp_client.get_result(message_text.strip(), tool_set):
            messages = util.chunk_string(util.to_html(llm_response))

        sent_message = await context.bot.send_message(
            chat_id=chat.id,
            text=messages[0],
            parse_mode=ParseMode.HTML,
            message_thread_id=command_message.message_thread_id,
            reply_to_message_id=command_message.id,
            disable_web_page_preview=True,
        )

        _ = await context.bot.delete_message(
            chat_id=chat.id,
            message_id=sent_sticker.message_id,
        )

    if env.AI_COMMAND_STICKER_REPLY == False:
        sent_message = await context.bot.send_message(
            chat_id=chat.id,
            text="Запрос отправлен LLM",
            parse_mode=ParseMode.HTML,
            message_thread_id=command_message.message_thread_id,
            reply_to_message_id=command_message.id,
        )

        messages = []
        for llm_response in mcp_client.get_result(message_text.strip(), tool_set):
            messages = util.chunk_string(util.to_html(llm_response))

            _ = await context.bot.edit_message_text(
                chat_id=chat.id,
                message_id=sent_message.message_id,
                text=messages[0],
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

    assert sent_message is not None

    prev_message = sent_message
    for text in messages[1:]:
        prev_message = await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            parse_mode=ParseMode.HTML,
            message_thread_id=command_message.message_thread_id,
            reply_to_message_id=prev_message.id,
            disable_web_page_preview=True,
        )
        await asyncio.sleep(1)


async def search_resources(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await ask_ai(update, context, SEARCH_COMMAND)


def get_tool_set_for_chat(
    chat_id: int,
    command_name: str,
) -> mcp_client.ToolSet | None:
    employment_mentoring_chat_id = int(env.EMPLOYMENT_MENTORING_CHAT_ID)
    global_chat_id = int(env.MAIN_CHANNEL_CHAT_ID)
    projects_group_work_chat_id = int(env.PROJECTS_GROUP_WORK_CHAT_ID)

    if command_name == SEARCH_COMMAND:
        if chat_id == global_chat_id or chat_id == projects_group_work_chat_id:
            return mcp_client.ToolSet.RESOURCES
        return None

    if chat_id == employment_mentoring_chat_id:
        return mcp_client.ToolSet.EMPLOYMENT_MENTORING
    if chat_id == global_chat_id or chat_id == projects_group_work_chat_id:
        return mcp_client.ToolSet.GLOBAL

    return None


def is_admin(user: ChatMember) -> bool:
    return (
        user.status == ChatMemberStatus.ADMINISTRATOR
        or user.status == ChatMemberStatus.OWNER
    )
