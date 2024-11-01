import os
import django
from django.contrib.auth import get_user_model
from django.core.management.utils import get_random_secret_key

# Устанавливаем DJANGO_SETTINGS_MODULE для работы с настройками
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGUevents.settings')
django.setup()

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# Получаем модель пользователя
User = get_user_model()

# Создаем суперпользователя, используя переменные окружения
username = os.getenv('SUPERUSER_NAME')
email = os.getenv('SUPERUSER_MAIL')
password = os.getenv('SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Суперпользователь {username} успешно создан.")
else:
    print(f"Суперпользователь {username} уже существует.")
    

