# SGUplatform

## Запуск на Linux:

1. Открыть терминал в PyCharm / VSCode.
2. Создание локального виртуального окружения:
   - Перейти в корневую папку, где находится SGUplatform.
   - Выполнить команду: `python3 -m venv venv`
   - Если возникает ошибка при создании окружения, выполните сначала:
     `sudo apt install python3.11-venv`
3. Активация виртуального окружения:
   - Перейти в корневую папку (где папка `venv`).
   - Выполнить команду: `source ./venv/bin/activate`
4. Перейти в папку проекта:
   - Выполнить команду: `cd ./SGUplatform`
5. Выбор интерпретатора Python:
   - Выбрать из папки виртуального окружения, которую создали.
   - Интерпретатор находится здесь: `...ваш_путь_к_venv/venv/bin/python3`
6. Установка всех пакетов. Находимся в директории SGUplatform (где лежит файл `requirements.txt`):
   - Выполнить команду: `pip3 install -r requirements.txt`
7. Создаем `.env` в корне с необходимыми переменными окружения.
8. Для локальной разработки собираем статику:
   - Выполнить команду: `python3 manage.py collectstatic --noinput`
9. Запуск проекта. Находимся в директории SGUplatform (где лежит файл `manage.py`):
   - Выполнить команду: `python3 manage.py runserver --noreload & python3 manage.py startbot --noreload`
   - Или настроить автоматический запуск (PyCharm - через Edit Configurations с параметром `runserver`, VSCode - через добавление `launch.json`).

## Запуск на Windows:

1. Открыть терминал (в PyCharm - внизу Terminal - alt+F12).
2. Создание локального виртуального окружения:
   - Перейти в корневую папку, где находится SGUplatform.
   - Выполнить команду: `python -m venv venv`
3. Активация виртуального окружения:
   - Перейти в корневую папку (где папка `venv`).
   - Выполнить команду: `\venv\Scripts\activate`
   - Если возникает ошибка: "Невозможно загрузить файл, так как выполнение сценариев отключено в этой системе", выполните следующие шаги:
     1. Открыть PowerShell от администратора.
     2. Ввести команду:
        `Set-ExecutionPolicy RemoteSigned`
4. Выбор интерпретатора Python:
   - Выбрать из папки виртуального окружения, которую создали.
   - Интерпретатор находится здесь: `...ваш_путь_к_venv\venv\Scripts\python`
5. Переходим в папку проекта SGUevents.
6. Установить пакеты с помощью команды:
   - Выполнить команду: `pip install -r requirements.txt`
7. Создаем `.env` в корне с необходимыми переменными окружения.
8. Для локальной разработки собираем статику:
   - Выполнить команду: `python manage.py collectstatic --noinput`
9. Запуск проекта. Находимся в директории SGUevents (где лежит файл `manage.py`):
   - Выполнить команду: `python manage.py runserver --noreload & python manage.py startbot --noreload`
   - Или настроить автоматический запуск (PyCharm - через Edit Configurations с параметром `runserver`, VSCode - через добавление `launch.json`).

## Запуск локально на Windows:

- Для работоспособности Telegram login Widget требуется [ngrok](https://dashboard.ngrok.com/get-started/setup/windows)
- Делаем по инструкции потом запускаем `ngrok http http://localhost:8000`
- Для запуска celery локально - запускаем Redis в докере `docker run --name redis -p 6379:6379 -d redis:latest`
- В одном окне из venv `celery -A SGUevents worker -l info -P solo` (-P solo - костыль для Windows)
- В другом окне аналогично `celery -A SGUevents beat -l info`

## Документация `/docs`

- Исходники находятся в `docs_src/`, конфигурация — `mkdocs.yml`, тема — Material.
- Доступные переменные окружения для контента: `SITE_DOMAIN`, `TG_BOT_URL`, `SUPPORT_EMAIL` (см. `docs_macros.py`). Добавляйте их в корневой `.env`, который уже подключён в `docker-compose.yml`.
- Локальный просмотр с хот-релоадом: `python -m mkdocs serve -f mkdocs.yml -a localhost:8088`.
- Для `site_url` можно задать `DOCS_SITE_URL` в `.env` (иначе берётся `https://events.sgu.ru/docs/`).
- Продакшн-сборка (итерируется в `static/docs`, откуда Django отдаёт `/docs`):
  - Linux/macOS: `scripts/build_docs.sh`
  - Windows: `powershell -ExecutionPolicy Bypass -File scripts/build_docs.ps1`
- Оба скрипта автоматически подхватывают переменные из `.env`, так что значения `SITE_DOMAIN`/`TG_BOT_URL`/`SUPPORT_EMAIL` не нужно экспортировать вручную.
- Перед деплоем убедитесь, что `scripts/build_docs.*` выполнены и обновлённый `static/docs` попал в репозиторий/артефакт, либо добавьте шаг `mkdocs build` в CI перед `collectstatic`.

## Заполнение БД:

- На windows вместо `python3` записывается просто `python`, вместо `/` используется `\`. При первой установке лучше удалить файл db.sqlite3 и все миграции в проекте (Пример: events_available/migrations/0001_initial.py)

1. Создаём миграцию для определения модели БД:
   - Выполнить команду: `python manage.py makemigrations`
2. Применяем созданную миграцию:
   - Выполнить команду: `python3 manage.py migrate`
3. Если удалялся файл db.sqlite3, то необходимо создать пользователя:
   - Выполнить команду: `python3 manage.py createsuperuser`
4. Загружаем информацию для страницы онлайн мероприятий:
   - Выполнить команду: `python3 manage.py loaddata fixtures/events_available/events_online.json`
5. Загружаем информацию для страницы оффлайн мероприятий:
   - Выполнить команду: `python3 manage.py loaddata fixtures/events_available/events_offline.json`
6. Загружаем информацию для страницы достопримечательности:
   - Выполнить команду: `python3 manage.py loaddata fixtures/events_cultural/attractions.json`
7. Загружаем информацию для страницы доступные к посещению:
   - Выполнить команду: `python3 manage.py loaddata fixtures/events_cultural/events_for_visiting.json`
8. Загружаем информацию об отделах:
   - Выполнить команду: `python3 manage.py loaddata fixtures/departments.json`

## При запуске на сервере:
1. Из каталога с файлом docker-compose.yml:
   - Выполнить команды: `docker-compose exec backend python manage.py makemigrations`
   - `docker-compose exec backend python manage.py migrate`
   - `docker-compose exec backend python manage.py collectstatic --noinput`
   - при невозможности применения миграций - сбрасывам таблицы:
   - `docker exec -it [id контейнера] bash`
   - `psql -U [db_user] -d [db_name]`
   - `DROP SCHEMA public CASCADE;`
   - `CREATE SCHEMA public;`
   - Для выхода из psql используйте команду \q, и для выхода из оболочки контейнера используйте exit.
   - Далее миграции, superuser и fixtures
