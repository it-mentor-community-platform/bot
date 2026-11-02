import logging
import re
from urllib.parse import urlsplit

import mistune
from typing import Any, override

from mistune.renderers.html import HTMLRenderer
from mistune.plugins.formatting import strikethrough
from mistune.plugins.table import table

from src.config import constants

MAX_MESSAGE_LENGTH = 4096

log = logging.getLogger(__name__)

PROJECT_RUSSIAN_NAMES = {
    constants.PROJECT_HANGMAN: "Виселица",
    constants.PROJECT_SIMULATION: "Симуляция",
    constants.PROJECT_CURRENCY_EXCHANGE: "Обмен валют",
    constants.PROJECT_TENNIS_SCOREBOARD: "Теннисное табло",
    constants.PROJECT_WEATHER_VIEWER: "Погода",
    constants.PROJECT_CLOUD_FILE_STORAGE: "Облачное хранилище файлов",
    constants.PROJECT_TASK_TRACKER: "Планировщик задач",
    "other": "Другое",
}


def normalize_github_repository_url(repository_url: str) -> str:
    candidate = repository_url.strip()
    if "://" not in candidate:
        candidate = "https://" + candidate

    parsed = urlsplit(candidate)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise ValueError("Not a GitHub repository URL")

    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError("GitHub repository URL must contain owner and repo")

    owner, repo = parts[:2]
    repo = repo.removesuffix(".git")

    if not owner or not repo:
        raise ValueError("Invalid GitHub repository owner or name")

    return f"https://github.com/{owner}/{repo}"


def escape_special_chars(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    pattern = "[" + re.escape(special_chars) + "]"

    escaped_text = re.sub(pattern, r"\\\g<0>", text)

    return escaped_text


def compress_messages(messages: list[str]) -> list[str]:
    compressed_messages: list[str] = []

    compressed_message = ""
    for message in messages:
        updated_compressed_message = compressed_message + "\n\n" + message

        if len(updated_compressed_message) < MAX_MESSAGE_LENGTH:
            compressed_message = updated_compressed_message
            continue

        if (
            len(updated_compressed_message) >= MAX_MESSAGE_LENGTH
            and len(compressed_message) < MAX_MESSAGE_LENGTH
        ):
            compressed_messages.append(compressed_message)
            compressed_message = message
            continue

    compressed_messages.append(compressed_message)

    return compressed_messages


def chunk_string(big_string: str) -> list[str]:
    chunks: list[str] = []

    if len(big_string) <= MAX_MESSAGE_LENGTH:
        return [big_string]

    current_chunk = ""
    lines = big_string.split("\n")

    for line in lines:
        if not current_chunk:
            current_chunk = line
            continue

        potential_chunk = current_chunk + "\n" + line

        if len(potential_chunk) <= MAX_MESSAGE_LENGTH:
            current_chunk = potential_chunk
        else:
            chunks.append(current_chunk)
            current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class TelegramRenderer(HTMLRenderer):
    _current_table: list[list[str]]
    _current_cells: list[str]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._current_table = []
        self._current_cells = []

    @override
    def text(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @override
    def link(self, text: str, url: str, title: str | None = None) -> str:
        return f'<a href="{url}">{text}</a>'

    @override
    def emphasis(self, text: str) -> str:
        return f"<i>{text}</i>"

    @override
    def strong(self, text: str) -> str:
        return f"<b>{text}</b>"

    @override
    def codespan(self, text: str) -> str:
        return f"<code>{text}</code>"

    @override
    def linebreak(self) -> str:
        return "\n"

    @override
    def softbreak(self) -> str:
        return "\n"

    @override
    def thematic_break(self) -> str:
        return "\n———\n"

    def strikethrough(self, text: str) -> str:
        return f"<s>{text}</s>"

    @override
    def paragraph(self, text: str) -> str:
        return text + "\n"

    @override
    def heading(self, text: str, level: int, **attrs: Any) -> str:
        return f"<b><u>{text}</u></b>\n"

    @override
    def blank_line(self) -> str:
        return "\n"

    @override
    def block_code(self, code: str, info: str | None = None) -> str:
        return f"<pre>{code}</pre>\n"

    @override
    def block_quote(self, text: str) -> str:
        return f"> {text}\n"

    @override
    def list(self, text: str, ordered: bool, **attrs: Any) -> str:
        return text + "\n"

    @override
    def list_item(self, text: str, **_: Any) -> str:
        return f"• {text}\n"

    def table_cell(
        self, text: str, align: str | None = None, head: bool = False
    ) -> str:
        self._current_cells.append(text.strip())
        return text

    def table_row(self, text: str) -> str:
        if self._current_cells:
            self._current_table.append(self._current_cells)
        self._current_cells = []
        return text

    def table(self, text: str) -> str:
        aligned = table_to_pre(self._current_table)
        self._current_table = []
        return f"<pre>{aligned}</pre>"

    def table_head(self, text: str) -> str:
        if self._current_cells:
            self._current_table.append(self._current_cells)
        self._current_cells = []
        return text

    def table_body(self, text: str) -> str:
        return text


renderer = TelegramRenderer()
markdown_parser = mistune.create_markdown(
    renderer=renderer, plugins=[strikethrough, table]
)


def to_html(text: str) -> str:
    html = markdown_parser(text)
    if isinstance(html, list):
        html = "".join(token.get("text", "") for token in html)
    return html


def table_to_pre(table: list[list[str]]) -> str:
    if not table:
        return ""

    num_cols = max(len(row) for row in table)
    col_widths = [0] * num_cols

    for row in table:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    lines: list[str] = []

    for i, row in enumerate(table):
        padded_cells = [(cell or "").ljust(col_widths[j]) for j, cell in enumerate(row)]
        lines.append("| " + " | ".join(padded_cells) + " |")

        if i == 0:
            sep = ["-" * w for w in col_widths]
            lines.append("| " + " | ".join(sep) + " |")

    return "\n".join(lines)
