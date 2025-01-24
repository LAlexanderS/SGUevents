import os
import subprocess
import sys

# Список файлов фикстур ё
fixtures = [
    'fixtures/departments.json',
    'fixtures/groups.json',
    'fixtures/users.json',
    'fixtures/events_available/events_offline.json',
    'fixtures/events_available/events_online.json',
    'fixtures/events_cultural/attractions.json',
    'fixtures/events_cultural/events_for_visiting.json',
    'fixtures/bookmarks/favorites.json',
    'fixtures/bookmarks/registered.json',
]

def load_fixtures():
    python_executable = sys.executable  # Получаем путь к текущему интерпретатору Python
    successful_fixtures = []
    failed_fixtures = []

    for fixture in fixtures:
        try:
            # Используем команду manage.py loaddata для загрузки каждой фикстуры
            subprocess.run([python_executable, 'manage.py', 'loaddata', fixture], check=True)
            print(f"Успешно загружен файл: {fixture}")
            successful_fixtures.append(fixture)
        except subprocess.CalledProcessError:
            print(f"Ошибка при загрузке файла: {fixture}")
            failed_fixtures.append(fixture)

    return successful_fixtures, failed_fixtures

if __name__ == '__main__':
    successful_fixtures, failed_fixtures = load_fixtures()

    if successful_fixtures:
        print("\nУспешно загруженные файлы:")
        for fixture in successful_fixtures:
            print(f"- {fixture}")
    else:
        print("\nНет успешно загруженных файлов.")

    if failed_fixtures:
        print("\nФайлы с ошибками:")
        for fixture in failed_fixtures:
            print(f"- {fixture}")
    else:
        print("\nНет ошибок при загрузке файлов.")
