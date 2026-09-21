from __future__ import annotations

import os

ENV_DEFAULTS = {
    "TELEGRAM_BOT_TOKEN": "test-token",
    "MAIN_CHANNEL_CHAT_ID": "1",
    "EMPLOYMENT_MENTORING_CHAT_ID": "2",
    "PROJECTS_REVIEWS_COLLECTION_CHAT_ID": "3",
    "PROJECTS_GROUP_WORK_CHAT_ID": "4",
    "ERRORS_CHAT_ID": "5",
    "MCP_SERVER_API_KEY": "test-key",
    "MCP_SERVER_URL": "http://mcp.test",
    "TEST_RUNNER_URL": "http://tests.test",
    "TEST_RUNNER_API_KEY": "test-key",
    "ADD_PROJECT_ALLOWED_USER_IDS": "100",
    "GOOGLE_SERVICE_ACCOUNT_JSON_KEY": "{}",
    "PROJECTS_REVIEWS_SPREADSHEET_ID": "test-sheet",
    "POSTGRES_USER": "test-user",
    "POSTGRES_PASSWORD": "test-password",
    "POSTGRES_DB": "test-db",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "JAVA_INTERVIEW_COLLECTION_SPREADSHEET_ID": "java-sheet",
    "PYTHON_INTERVIEW_COLLECTION_SPREADSHEET_ID": "python-sheet",
    "SEARCH_INTERVIEW_QUESTIONS_COMMAND_CHAT_IDS": "1",
    "INTERVIEW_PREP_SITE_REPO_OWNER": "owner",
    "INTERVIEW_PREP_SITE_REPO_NAME": "repo",
    "JAVA_BACKEND_COURSE_SITE_REPO_OWNER": "owner",
    "JAVA_BACKEND_COURSE_SITE_REPO_NAME": "repo",
    "PYTHON_BACKEND_COURSE_SITE_REPO_OWNER": "owner",
    "PYTHON_BACKEND_COURSE_SITE_REPO_NAME": "repo",
    "GOLANG_BACKEND_COURSE_SITE_REPO_OWNER": "owner",
    "GOLANG_BACKEND_COURSE_SITE_REPO_NAME": "repo",
    "GITHUB_COMMUNITY_BOT_ACCESS_TOKEN": "test-token",
    "QUESTIONS_POPULARITY_UPDATE_ALLOWED_USER_IDS": "1",
    "METRICS_USER": "test-user",
    "METRICS_PASS": "test-password",
    "METRICS_PORT": "8001",
    "DEFAULT_LLM_MODEL": "test-model",
    "BIGGER_CONTEXT_LLM_MODEL": "test-model-big",
    "COMMUNITY_BACKEND_INTEGRATION_ROOT_URL": "http://backend.test",
    "COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME": "test-user",
    "COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD": "test-password",
}

for key, value in ENV_DEFAULTS.items():
    os.environ[key] = value
