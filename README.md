# Bot

Будущий основной интерфейс взаимодействия с платформой сообщества

## Стэк

- Python == 3.12 (строго 3.12)
- PostgreSQL
- [Python Telegram Bot](https://docs.python-telegram-bot.org/en/stable)
- [Yoyo migrations](https://ollycope.com/software/yoyo/latest)
- [gspread](https://docs.gspread.org/en/latest/index.html)
- [OpenAI Python SDK](https://github.com/openai/openai-python)

## Документация

- [Описание интеграции с основным бэкендом платформы](https://github.com/it-mentor-community-platform/meta/blob/main/system-analytics/telegram-bot-integration.md)
- [Описание REST API адаптера](https://github.com/it-mentor-community-platform/meta/blob/main/system-analytics/services/telegram-bot-adapter/index.md)

## Функционал

1. Добавление проектов в таблицу [Проекты и ревью](https://docs.google.com/spreadsheets/d/1E66YrdvO7B_j0Ykge-JJDMtB1RfKhIzN_SsO7UPDbrU); `/addproject`
2. Генерация сообщения итогов месяца по сданным проектам по данным из таблицы [Проекты и ревью](https://docs.google.com/spreadsheets/d/1E66YrdvO7B_j0Ykge-JJDMtB1RfKhIzN_SsO7UPDbrU); `projectsmonthlysummary`
3. Генерация сообщения итогов месяца по сделанным ревью по данным из таблицы [Проекты и ревью](https://docs.google.com/spreadsheets/d/1E66YrdvO7B_j0Ykge-JJDMtB1RfKhIzN_SsO7UPDbrU); `reviewsmonthlysummary`
4. Генерация сообщений со списком вопросов по данным из таблицы [Java методичка](https://docs.google.com/spreadsheets/d/1mcTcg9dR7Hv265h4ei5Ioyx9V94SnhCCYcG4zNo2bAk), которая служит источником данных для сайта [Java методичка](https://zhukovsd.github.io/java-backend-interview-prep); `/interviewprepquestionslist`
5. Генерация сообщений со списком вопросов по данным из таблицы [Python методичка](https://docs.google.com/spreadsheets/d/1qVIahkSxHPFEAmMAzNNLvBUD8pe4oaG0fG6A_LZaPoc), которая служит источником данных для сайта [Python методичка](https://zhukovsd.github.io/python-backend-interview-prep); `/interviewprepquestionslist`
6. Генерация сообщения со списком собеседований на которых задавали конкретный вопрос по данным из таблиц [Java методичка](https://docs.google.com/spreadsheets/d/1mcTcg9dR7Hv265h4ei5Ioyx9V94SnhCCYcG4zNo2bAk) и [Python методичка](https://docs.google.com/spreadsheets/d/1qVIahkSxHPFEAmMAzNNLvBUD8pe4oaG0fG6A_LZaPoc); `/q`, `/qp`
7. Добавление новых проектов и ревью в [Репозиторий Java роадмапа](https://github.com/zhukovsd/java-backend-learning-course) через PR c помощью [аккаунта бота](https://github.com/zhukovsd-it-mentor-community-bot) на основании данных из таблицы [Проекты и ревью](https://docs.google.com/spreadsheets/d/1E66YrdvO7B_j0Ykge-JJDMtB1RfKhIzN_SsO7UPDbrU); `/updatefinishedprojects`
8. Добавление новых проектов и ревью в [Репозиторий Python роадмапа](https://github.com/zhukovsd/python-backend-learning-course) через PR c помощью [аккаунта бота](https://github.com/zhukovsd-it-mentor-community-bot) на основании данных из таблицы [Проекты и ревью](https://docs.google.com/spreadsheets/d/1E66YrdvO7B_j0Ykge-JJDMtB1RfKhIzN_SsO7UPDbrU); `/updatefinishedprojects`
9. Добавление новых проектов и ревью в [Репозиторий Go роадмапа](https://github.com/zhukovsd/golang-backend-learning-course) через PR c помощью [аккаунта бота](https://github.com/zhukovsd-it-mentor-community-bot) на основании данных из таблицы [Проекты и ревью](https://docs.google.com/spreadsheets/d/1E66YrdvO7B_j0Ykge-JJDMtB1RfKhIzN_SsO7UPDbrU); `/updatefinishedprojects`
10. Пересылка запроса юзера в MCP сервер сообщества (приватный репозиторий); `/ai`
11. [**В процессе разработки**] Запуск REST API тестов для задеплоенного проекта роадмапа с помощью отдельного [test-runner'а](https://github.com/zhukovsd/roadmap-projects-api-tests-runner); `/runtests`


[**Deprecated**] Обновления популярности списка вопросов в [Репозитории Java методичка](https://github.com/zhukovsd/java-backend-interview-prep), который служит источником данных для сайта [Java методички](https://zhukovsd.github.io/java-backend-interview-prep) через PR c помощью [аккаунта бота](https://github.com/zhukovsd-it-mentor-community-bot) на основании данных из таблицы [Java методичка](https://docs.google.com/spreadsheets/d/1mcTcg9dR7Hv265h4ei5Ioyx9V94SnhCCYcG4zNo2bAk)

## Сетап секретов

Основные секреты должны быть доступны на доске [local-stack-secrets](https://github.com/orgs/it-mentor-community-platform/projects/9)

Секреты с комментариями "доступны по запросу" выдаются отдельно

Для локального тестирования любой команды которая затрагивает Google таблицы нужно сделать следующее:

1. Открыть оригинальную таблицу
2. В меню выбрать `Файл` -> `Создать копию`
3. Из адресной строки новой таблицы скопировать ID (между `/d/` и `/edit`)
4. Добавить ID копии таблицы в `.env` файл
5. Скопировать `client_email` поле сервисного аккаунта (выглядит как `name@project.iam.gserviceaccount.com`) из `.env` файла
6. Открыть копию таблицы в браузере, нажать `Поделиться` и добавить этот email с правами `Редактор`

Для локального тестирования любой команды которая затрагивает GitHub репозитории нужно сделать следующее:

1. Открыть ссылку на оригинальный репозиторий
2. Нажать кнопку `Fork`
3. Поставить переменную окружения для соответствующего репозитория в `.env` файле
4. Перейти в `Settings` -> `Collaborators` -> `Add people`
5. Найти в поиске и добавить [it-mentor-community-bot-dev](https://github.com/it-mentor-community-bot-dev)
6. Пингануть `@krios2146` в чате командного проекта (владелец аккаунта `it-mentor-community-bot-dev`)
7. Ожидать принятия реквеста коллаборатора

## Локальный запуск 

1. Создать venv

```sh
python -m venv venv
```

2. Активировать venv (если pycharm не сделал это автоматически) 

```sh
source venv/bin/activate
```

https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html#widget

3. Установить зависимости (если pycharm не сделал это автоматически)

```sh
pip install -r requirements.txt
```

4. Создать `.env` файл в корне проекта. Он будет использоваться только для локального запуска. Структура представлена в `.example.env` файле

5. Поднять БД в контейнере командой

```sh
docker compose -f docker-compose-dev.yaml up -d
```

6. Сделать миграцию для БД. Использовать те же данные, которые указаны в `.env` файле

```sh
yoyo apply --database postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} ./migrations
```
Чтобы переменные в команде подставились автоматически, перед выполнением нужно сделать `source .env`

Либо просто вручную подставить значения из `.env` вместо `${POSTGRES_USER}`:

```sh
yoyo apply --database postgresql://user:password@localhost:5433/it-mentor-community-bot-database ./migrations
```

7. Запустить проект

 - C помощью UI pycharm
 - Через `python -m src.main`
