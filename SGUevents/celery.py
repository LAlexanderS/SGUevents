from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
import logging
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGUevents.settings')

app = Celery('SGUevents')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    beat_schedule={
        'schedule_notifications': {
            'task': 'bookmarks.tasks.schedule_notifications',
            'schedule': crontab(minute='*/1'),  # Запускать каждую минуту
        },
    },
)

logger = logging.getLogger('my_debug_logger')

@app.task(bind=True)
def check_deleted_message(self, media_file_id: int):
    """
    Проверяет, было ли удалено сообщение с медиафайлом из чата Telegram.
    Если сообщение удалено, удаляет файл с Яндекс.Диска.
    """
    from events_available.models import MediaFile
    from django.conf import settings
    import yadisk
    from aiogram import Bot
    import asyncio

    try:
        media_file = MediaFile.objects.get(id=media_file_id)
        
        # Инициализация бота
        bot = Bot(token=settings.ACTIVE_TELEGRAM_BOT_TOKEN)
        
        # Пытаемся получить сообщение
        try:
            message = asyncio.run(bot.get_message(
                chat_id=media_file.chat_id,
                message_id=int(media_file.message_id)
            ))
            logger.info(f"Сообщение {media_file.message_id} существует в чате {media_file.chat_id}")
            # Если сообщение существует, завершаем задачу
            media_file.celery_task_id = None
            media_file.save()
            return "Message exists, task completed"
            
        except Exception as e:
            logger.info(f"Сообщение {media_file.message_id} было удалено из чата {media_file.chat_id}")
            # Если сообщение не найдено, удаляем файл с Яндекс.Диска
            y = yadisk.YaDisk(
                id=settings.YANDEX_DISK_CLIENT_ID,
                secret=settings.YANDEX_DISK_CLIENT_SECRET,
                token=settings.YANDEX_DISK_OAUTH_TOKEN
            )
            
            try:
                if y.exists(media_file.file_path):
                    y.remove(media_file.file_path, permanently=True)
                    logger.info(f"Файл {media_file.file_path} удален с Яндекс.Диска")
            except Exception as e:
                logger.error(f"Ошибка при удалении файла с Яндекс.Диска: {e}")
            
            # Отмечаем файл как удаленный
            media_file.is_deleted = True
            media_file.celery_task_id = None
            media_file.save()
            return "File deleted from Yandex.Disk"
            
    except MediaFile.DoesNotExist:
        logger.error(f"MediaFile с id {media_file_id} не найден")
        return "MediaFile not found"
    except Exception as e:
        logger.error(f"Ошибка при проверке удаленного сообщения: {e}")
        return f"Error: {str(e)}"

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
