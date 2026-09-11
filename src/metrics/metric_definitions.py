from prometheus_client import Counter

telegram_command_usage_total = Counter(
    "telegram_command_usage_total",
    "Total number of times a telegram command was used",
    ["command"]
)

openai_tokens_usage_total = Counter(
    "openai_tokens_usage_total",
    "Total number of OpenAI tokens consumed",
    ["token_type", "model"]
)

openai_spend_usd_total = Counter(
    'openai_spend_usd_total',
    "Total money spent on OpenAI API in USD",
    ["model"]
)

telegram_errors_total = Counter(
    "telegram_errors_total",
    "Total number of unhandled exceptions caught by the error handler",
    ["exception_type"]
)

telegram_tasks_processed_total = Counter(
    "telegram_tasks_processed_total",
    "Total number of successfully processed Telegram tasks",
    ["task_type"]
)