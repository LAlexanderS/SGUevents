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
7. Создаем `.env` в корне по образцу `.env.example`.
8. Запуск проекта. Находимся в директории SGUplatform (где лежит файл `manage.py`):
    - Выполнить команду: `python3 manage.py runserver`
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
7. Создаем `.env` в корне по образцу `.env.example`.
8. Запуск проекта. Находимся в директории SGUevents (где лежит файл `manage.py`):
    - Выполнить команду: `python manage.py runserver`
    - Или настроить автоматический запуск (PyCharm - через Edit Configurations с параметром `runserver`, VSCode - через добавление `launch.json`).

## Запуск из Docker (пока локально на Windows):

- Запустите Docker desktop для Windows.
- Выполните следующие команды:
    ```
    docker-compose build
    docker-compose up -d
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser
    ```
