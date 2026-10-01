import logging
from collections.abc import Generator
from enum import Enum

from openai.types import ResponsesModel
from openai.types.responses import response_create_params

from src.config import env
from src.mcp import openai

log = logging.getLogger(__name__)

default_model: ResponsesModel = env.DEFAULT_LLM_MODEL
bigger_context_model: ResponsesModel = env.BIGGER_CONTEXT_LLM_MODEL


ToolSet = Enum("ToolSet", ["EMPLOYMENT_MENTORING", "GLOBAL", "RESOURCES"])

employment_mentoring_tools = ["find_interviews", "find_interview_questions"]
global_tools = ["find_interview_questions_limited"]
resource_tools = ["find_resources"]

max_interviews = 50


def get_result(
    user_input: str,
    tool_set: ToolSet,
) -> Generator[str, None, None]:
    allowed_tools: list[str] | None = None
    tool_choice: response_create_params.ToolChoice = "auto"

    if tool_set == ToolSet.EMPLOYMENT_MENTORING:
        allowed_tools = employment_mentoring_tools
    if tool_set == ToolSet.GLOBAL:
        allowed_tools = global_tools
    if tool_set == ToolSet.RESOURCES:
        allowed_tools = resource_tools
        tool_choice = "required"

    if allowed_tools is None:
        yield "Нет подходящих инструментов для текущего запроса"
        return

    try:
        response = openai.call_llm(
            user_input, allowed_tools, default_model, tool_choice
        )
        yield f"{response}\n\nИспользована модель: {default_model}"

    except openai.ContextExceededError as e:
        try:
            log.warning(f"{e}")
            yield f"Модель {default_model} не выдержала контекста запроса, пробуем {bigger_context_model}"

            response = openai.call_llm(
                user_input, allowed_tools, bigger_context_model, tool_choice
            )
            yield f"{response}\n\nИспользована модель: {bigger_context_model}"

        except openai.ContextExceededError as e:
            if tool_set == ToolSet.RESOURCES:
                yield "Контекст запроса превышен"
                return

            yield f"Модель {bigger_context_model} не выдержала контекста запроса, пробуем ограничить выборку {max_interviews} собесами"
            user_input = f"{user_input}\n\n**FETCH ONLY {max_interviews} INTERVIEWS REGARDLESS OF WHAT IS WRITTEN ABOVE**"

            try:
                response = openai.call_llm(
                    user_input, allowed_tools, bigger_context_model, tool_choice
                )
                yield f"{response}\n\nИспользована модель: {bigger_context_model} c ограничением выборки {max_interviews} собесами"
            except openai.ContextExceededError as e:
                yield "Контекст запроса превышен"
