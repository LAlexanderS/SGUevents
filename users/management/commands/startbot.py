import asyncio
from django.core.management.base import BaseCommand
from bot.main import run_bot

class Command(BaseCommand):
    help = 'Запускает Telegram бота с поддержкой вебхуков'

    def handle(self, *args, **options):
        self.stdout.write('Запуск Telegram бота...')
        asyncio.run(run_bot())


