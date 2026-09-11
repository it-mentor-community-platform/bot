## Информация

> [!IMPORTANT]  
> Проект разработан на версии python == 3.12, работоспособность на других версиях не гарантируется (на 3.13 проект не запускается)

- Создание бота и получение токена - https://t.me/BotFather
- При создании бота нужно отправить BotFather команду `/setinline`, иначе бот не будет работать через `@` в чате
- Бот должен быть админом в чатах в которых вызываются его команды и в чате в который он будет пересылать сообщения
- [yoyo-migrations документация](https://ollycope.com/software/yoyo/latest/)

### Как Получить JSON токен google API для подключения?

[gspread auth docs](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account)

Для этого Нужно перейти на:

- https://console.cloud.google.com/projectselector2/apis/dashboard?supportedpurview=project
- Далее в: API & Services > Переходим: Credentials > Создаем: Create credentials > Service account key
- Заполняем все необходимые поля
- Нажимаем Done 
- Нажимаем “Manage service accounts” над Service Accounts.
- В открывшейся таблице кликаем 3 точки > Manage Keys
- ADD KEY > Create new key > JSON

Мы получим JSON файл с API Key

##### Обязательно

Нужно будет добавить к пользователям Email из API Key в ключе `client_email`
Делать это стоит конкретно к таблице с которой мы будем работать, либо к папке с таблицами в которой мы будем работать

Также надо перейти в 

- API & Services > Library
- Ввести `Google Drive API` и `Google Sheets API` в поиск
- И включить эти две либы (Нажать Enable) 

## Локальный запуск 

1. Создать venv

```bash
python -m venv venv
```

2. Активировать venv (если pycharm не сделал это автоматически) 

```bash
source venv/bin/activate
```

https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html#widget

3. Установить зависимости (если pycharm не сделал это автоматически) 

```bash
pip install -r requirements.txt
```

4. Создать `.env` файл в корне проекта. Он будет использоваться только для локального запуска

```env
TELEGRAM_BOT_TOKEN=

POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=

MAIN_CHANNEL_CHAT_ID=
EMPLOYMENT_MENTORING_CHAT_ID=
PROJECTS_REVIEWS_COLLECTION_CHAT_ID=

MCP_SERVER_API_KEY=
MCP_SERVER_URL=

TEST_RUNNER_URL=
TEST_RUNNER_API_KEY=

ADD_PROJECT_ALLOWED_USER_IDS=

GOOGLE_SERVICE_ACCOUNT_JSON_KEY=
PROJECTS_REVIEWS_SPREADSHEET_ID=
JAVA_INTERVIEW_COLLECTION_SPREADSHEET_ID=
PYTHON_INTERVIEW_COLLECTION_SPREADSHEET_ID=

SEARCH_INTERVIEW_QUESTIONS_COMMAND_CHAT_IDS=

INTERVIEW_PREP_SITE_REPO_OWNER=
INTERVIEW_PREP_SITE_REPO_NAME=

JAVA_BACKEND_COURSE_SITE_REPO_OWNER=
JAVA_BACKEND_COURSE_SITE_REPO_NAME=

PYTHON_BACKEND_COURSE_SITE_REPO_OWNER=
PYTHON_BACKEND_COURSE_SITE_REPO_NAME=

GOLANG_BACKEND_COURSE_SITE_REPO_OWNER=
GOLANG_BACKEND_COURSE_SITE_REPO_NAME=

GITHUB_COMMUNITY_BOT_ACCESS_TOKEN=

QUESTIONS_POPULARITY_UPDATE_ALLOWED_USER_IDS=

SEND_PROJECTS_TO_CHAT=
```

`PROJECTS_REVIEWS_SPREADSHEET_ID` - Строка без пробелов содержащая в себе id файла google sheet из google drive который подключается с помощью google api.
- id достается из url самой таблицы при открытии в браузере на ПК
`ADD_PROJECT_ALLOWED_USER_IDS` - Список id юзеров, которые могут пользоваться командой. Указывается через запятую без пробелов = 322,511,987
`PROJECTS_REVIEWS_COLLECTION_CHAT_ID` - ID Чата куда пересылаем ответное сообщение. Указывать можно в виде списка по аналогии с 
`ADD_PROJECT_ALLOWED_USER_IDS`
- **Не добавлять сюда** ID другого **чат бота** или того же самого который используется

`GOOGLE_SERVICE_ACCOUNT_JSON_KEY` - JSON строка формата:
```json
{
  "type": "service_account",
  "project_id": "it-menthor-community-bot",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "",
  "token_uri": "",
  "auth_provider_x509_cert_url": "",
  "client_x509_cert_url": "",
  "universe_domain": ""
}
```

`INTERVIEW_PREP_SITE_REPO_OWNER` - Владелец репозитория с методичкой
`INTERVIEW_PREP_SITE_REPO_NAME` - Название репозитория с методичкой

`JAVA_BACKEND_COURSE_SITE_REPO_OWNER` - Владелец репозитория с java роадмапом
`JAVA_BACKEND_COURSE_SITE_REPO_NAME` - Название репозитория с java роадмапом

`PYTHON_BACKEND_COURSE_SITE_REPO_OWNER` - Владелец репозитория с python роадмапом
`PYTHON_BACKEND_COURSE_SITE_REPO_NAME` - Название репозитория с python роадмапом

`GOLANG_BACKEND_COURSE_SITE_REPO_OWNER` - Владелец репозитория с go роадмапом
`GOLANG_BACKEND_COURSE_SITE_REPO_NAME` - Название репозитория с go роадмапом

`GITHUB_COMMUNITY_BOT_ACCESS_TOKEN` - Classic token авторизации GitHub аккаунта бота с которого будет создаваться PR в репозиторий методички. Обязательный scope - repo. Аккаунт бота должен иметь роль collaborator в настройках репозитория куда он должен сделать PR

`QUESTIONS_POPULARITY_UPDATE_ALLOWED_USER_IDS` - Юзеры, которые могут пользоваться командой обновления популярности вопросов. Указывается через запятую без пробелов = 322,511,987

`SEND_PROJECTS_TO_CHAT` - Контролирует нужно ли пересылать сообщения пользователей в чат указанный в `PROJECTS_REVIEWS_COLLECTION_CHAT_ID` при использовании команды /addproject. Любое значение кроме `true` расценивается как `false`. Дефолтное значение `false`

`METRICS_USER` - Имя пользователя, которое надо ввести для доступа к странице /metrics

`METRICS_PASS` - Пароль для доступа к странице /metrics

`DEFAULT_LLM_MODEL` - Основная модель для повседневных задач

`BIGGER_CONTEXT_LLM_MODEL` - Модель с увеличенным контекстным окном

`COMMUNITY_BACKEND_INTEGRATION_ENABLED`- Флаг для включения или выключения интеграции с сервисом-адаптером (`true` — интеграция работает, `false` — фоновый опрос отключен).

`COMMUNITY_BACKEND_INTEGRATION_ROOT_URL`- Базовый веб-адрес (URL) сервиса-адаптера

`COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_USERNAME`- Логин для авторизации в REST API адаптера по протоколу Basic Auth

`COMMUNITY_BACKEND_INTEGRATION_BASIC_AUTH_PASSWORD`- Пароль для авторизации в REST API адаптера по протоколу Basic Auth

5. Поднять БД в контейнере командой

```bash
docker compose -f docker-compose-dev.yaml up -d
```

6. Сделать миграцию для БД. Использовать те же данные, которые указаны в `.env` файле

```bash
yoyo apply --database postgresql://user:password@localhost:5433/database-name ./migrations
```

7. Запустить проект

 - C помощью UI pycharm
 - Через `python -m src.main`

---

## Запуск в докере 

1. Создать `.env.prod` файл в корне проекта. 

`.env.prod` аналогичен `.env` файлу описанному в [4 пункте локального запуска](#локальный-запуск)

2. Собрать образ бота

```bash
docker build -t zhukovsd/it-mentor-community-bot:main .
```

3. Запустить бота и БД в докер композ

```bash
docker compose -f docker-compose-prod.yaml --env-file .env.prod up -d
```
