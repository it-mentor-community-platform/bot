from pg import DB

from src.config.env import (
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PORT,
)

db = DB(
    dbname=POSTGRES_DB,
    host=POSTGRES_HOST,
    port=int(POSTGRES_PORT),
    user=POSTGRES_USER,
    passwd=POSTGRES_PASSWORD,
)


def find_reply_by_language_and_project(language: str, project: str) -> str | None:
    query = db.query(f"""
        SELECT message, language FROM "Add_project_replies" 
        WHERE project_name='{project}'
        """)
    rows = query.dictresult()

    rows_by_language = list(filter(lambda x: x["language"] == language, rows))

    if len(rows_by_language) == 1:
        return rows_by_language[0]["message"]

    rows_by_language = list(filter(lambda x: x["language"] == "*", rows))

    if len(rows_by_language) == 1:
        return rows_by_language[0]["message"]

    return None
