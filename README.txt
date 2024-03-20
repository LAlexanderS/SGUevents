Создать папку SGUplatform и установить проект 

Запуск на Linux:
1) Открыть терминал в PyCharm / VSCode
2) Создание локального виртуального окружения 
	перейти в корневую папку, где находится SGUplatform. Далее, 
	команда:  python3 -m venv venv
	если ошибка при создании окружения, то сначала
	команда: sudo apt install python3.11-venv
3) Активация виртуального окружения 
	перейти в корневую папку (где папка venv)
	команда: source ./venv/bin/activate
4) Переходим в папку проекта 
	команда: cd ./SGUplatform
5) Выбор интерпретатора python:
	Выбрать из папки виртуального окружения, которую создали. 
	Интерпретатор лежит тут: ...your_path_to_venv/venv/bin/python3
6) Установка всех пакетов. Находимся в директории SGUplatform (где лежит файл requirements.txt):
	команда: pip3 install -r requirements.txt
7) Создаем .env в корне по образцу .env.example
8) Запуск проекта. Находимся в директории SGUplatform (где лежит файл manage.py)
	команда: python3 manage.py runserver

	или настроить автоматический запуск (PyCharm - через EditConfigurations с параметром runserver VSCode - через добавление launch.json )


Запуск на Windows:
1) Отркыть терминал (в PyCharm - внизу Terminal - alt+F12). 
2) Создание локального виртуального окружения 
	перейти в корневую папку, где находится SGUplatform. Далее, 
	команда:  python -m venv venv
3) Активация виртуального окружения 
	перейти в корневую папку (где папка venv)
	команда: \venv\Scripts\activate

	Если ошибка:  Невозможно загрузить файл , так как выполнение сценариев отключено в этой системе. Для получения дополн
ительных сведений см. about_Execution_Policies по адресу https:/go.microsoft.com/fwlink/?LinkID=135170, то нужно:
	1. Открываем PowerShell от админа 
	2. Пишем команду:
	Set-ExecutionPolicy RemoteSigned	
	
4) Выбор интерпретатора python:
	Выбрать из папки виртуального окружения, которую создали. 
	Интерпретатор лежит тут: ...your_path_to_venv\venv\Scripts\python
5) Переходим в папку проекта SGUevents
6) Установить пакеты с помощью команды 
	команда: pip install -r requirements.txt
7) Создаем .env в корне по образцу .env.example
8) Запуск проекта. Находимся в директории SGUevents (где лежит файл manage.py)
	python manage.py runserver 

	или настроить автоматический запуск (PyCharm - через EditConfigurations с параметром runserver VSCode - через добавление launch.json )
	
