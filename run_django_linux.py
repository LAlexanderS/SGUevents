import subprocess
import os
import sys
import time
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Команда {command} успешно выполнена.")
    else:
        print(f"Ошибка при выполнении команды {command}: {result.stderr}")
        sys.exit(1)

def recreate_postgres_db():
    try:
        # Подключаемся к базе postgres
        conn = psycopg2.connect(
            dbname='postgres',  
            user=os.getenv("LOCAL_DB_USER"),
            password=os.getenv("LOCAL_DB_PASSWORD"),
            host=os.getenv("LOCAL_DB_HOST"),
            port=os.getenv("LOCAL_DB_PORT")
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Завершаем активные подключения к базе данных, которую нужно удалить
        print("Завершаем активные подключения к базе данных...")
        cursor.execute(sql.SQL("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
            AND pid <> pg_backend_pid();
        """), [os.getenv("LOCAL_DB_NAME")])

        # Проверяем, что все процессы завершены
        time.sleep(2)  # Даем немного времени для завершения процессов
        cursor.execute("""
            SELECT count(*) FROM pg_stat_activity WHERE datname = %s;
        """, [os.getenv("LOCAL_DB_NAME")])
        result = cursor.fetchone()
        
        if result[0] > 0:
            print(f"Не удалось завершить все подключения к базе данных: {result[0]} активных подключений.")
            sys.exit(1)

        # Удаление базы данных
        print("Удаляем базу данных...")
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(os.getenv("LOCAL_DB_NAME"))))

        # Создание новой базы данных
        print("Создаем базу данных заново...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(os.getenv("LOCAL_DB_NAME"))))

        cursor.close()
        conn.close()
        print(f"База данных {os.getenv('LOCAL_DB_NAME')} успешно пересоздана.")
    except Exception as e:
        print(f"Ошибка при перезапуске базы данных PostgreSQL: {e}")
        sys.exit(1)

def create_extensions():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("LOCAL_DB_NAME"),  
            user=os.getenv("LOCAL_DB_USER"),
            password=os.getenv("LOCAL_DB_PASSWORD"),
            host=os.getenv("LOCAL_DB_HOST"),
            port=os.getenv("LOCAL_DB_PORT")
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Устанавливаем расширение pg_trgm
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

        # Устанавливаем расширение unaccent и создаем конфигурацию russian_conf
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        cursor.execute("CREATE TEXT SEARCH CONFIGURATION russian_conf ( COPY = russian );")
        cursor.execute("ALTER TEXT SEARCH CONFIGURATION russian_conf "
                       "ALTER MAPPING FOR hword, hword_part, word WITH unaccent, russian_stem;")

        cursor.close()
        conn.close()
        print("Расширения pg_trgm и unaccent, а также конфигурация russian_conf успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании расширений и конфигураций: {e}")
        sys.exit(1)

# Перезапуск базы данных
recreate_postgres_db()

# Установка расширений
create_extensions()

# Выполнение остальных команд
run_command('python3 delete_migrations.py')
run_command('python3 manage.py makemigrations')
run_command('python3 manage.py migrate')
run_command('python3 load_fixtures.py')

# Создание суперпользователя
create_superuser_command = """
from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username='Admin').exists():
    User.objects.create_superuser(email='ad@min.com', password='root', username='Admin')
else:
    print('Суперпользователь уже существует.')
"""

with open('create_superuser.py', 'w') as f:
    f.write(create_superuser_command)

run_command('python3 manage.py shell -c "exec(open(\'create_superuser.py\').read())"')

os.remove('create_superuser.py')
print('Суперпользователь успешно создан.')

# Запуск сервера
subprocess.run('python3 manage.py runserver', shell=True)
