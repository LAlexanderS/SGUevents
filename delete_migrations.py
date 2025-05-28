#Скрипт для удаления старых миграций. Автоматически испольузется в run_django_linux.py 

import os
import shutil

project_dir = os.path.dirname(os.path.abspath(__file__))
apps = [d for d in os.listdir(project_dir) if os.path.isdir(os.path.join(project_dir, d)) and not d.startswith('.')]

for app in apps:
    migrations_dir = os.path.join(project_dir, app, 'migrations')
    if os.path.exists(migrations_dir):
        for root, dirs, files in os.walk(migrations_dir):
            for file in files:
                if file != '__init__.py':
                    os.remove(os.path.join(root, file))
        print(f'Migrations deleted in {app}')
    else:
        print(f'No migrations found in {app}')
