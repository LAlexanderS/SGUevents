import os

from celery.schedules import crontab
from dotenv import load_dotenv
from pathlib import Path
import logging
import logging.config

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', default='p&l%385148kslhtyn^##a1)ilz@4zqj=rq&agdol^##zgl9(vs')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'main',
    'users',
    'events_available',
    'events_calendar',
    'events_cultural',
    'bookmarks',
    'application_for_admin_rights',
    'support',
    'personal',
    'debug_toolbar',
    'SGUevents',
    'django_celery_beat',
    ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'SGUevents.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SGUevents.wsgi.application'

# Значение по умолчанию для разработки
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

# Токены для разработки и продакшена
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEV_BOT_TOKEN = os.getenv("TELEGRAM_DEV_BOT_TOKEN")
ADMIN_TG_NAME = os.getenv("ADMIN_TG_NAME")
DEV_SUPPORT_CHAT_ID = os.getenv("DEV_SUPPORT_CHAT_ID")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

# Выбор активного токена на основе окружения
ACTIVE_TELEGRAM_BOT_TOKEN = TELEGRAM_DEV_BOT_TOKEN if DJANGO_ENV == 'development' else TELEGRAM_BOT_TOKEN
ACTIVE_TELEGRAM_SUPPORT_CHAT_ID = DEV_SUPPORT_CHAT_ID if DJANGO_ENV == 'development' else SUPPORT_CHAT_ID

if DJANGO_ENV == 'development':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('LOCAL_DB_NAME'),
            'USER': os.getenv('LOCAL_DB_USER'),
            'PASSWORD': os.getenv('LOCAL_DB_PASSWORD'),
            'HOST': os.getenv('LOCAL_DB_HOST', 'localhost'),
            'PORT': os.getenv('LOCAL_DB_PORT', '5432'),
        }
    }
elif DJANGO_ENV == 'devo':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('POSTGRES_USER'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('DB_HOST', default='db'),
            'PORT': os.getenv('DB_PORT'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Security settings for HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Novosibirsk'

USE_I18N = True

USE_TZ = True

LOGIN_URL = 'users:login'

AUTH_USER_MODEL = 'users.User'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# Static files settings
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = 'media/'

MEDIA_ROOT = BASE_DIR / 'media'

INTERNAL_IPS = [
    "127.0.0.1",
    # ...
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Novosibirsk'
CELERY_ENABLE_UTC = False

CELERY_BEAT_SCHEDULE = {
    'schedule-notifications-every-hour': {
        'task': 'bookmarks.tasks.schedule_notifications',
        'schedule': crontab(minute=0),  # запуск каждый час
    },
    'schedule-notifications-every-10-minutes': {
        'task': 'bookmarks.tasks.schedule_notifications',
        'schedule': crontab(minute='*/10'),  # запуск каждые 10 минут
    },
    'schedule-notifications-every-minute': {
        'task': 'bookmarks.tasks.schedule_notifications',
        'schedule': crontab(minute='*/1'),  # запуск каждую минуту
    },
}

# Настройки логирования (раскомментировать, если нужно)
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'DEBUG',
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'celery': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'bookmarks': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#     },
# }
