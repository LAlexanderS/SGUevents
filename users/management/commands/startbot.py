import asyncio
from django.core.management.base import BaseCommand
from bot.main import run_bot

class Command(BaseCommand):
    help = 'Запускает Telegram бота с поддержкой вебхуков'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noreload',
            action='store_true',
            help='Отключить автоматическую перезагрузку Django при изменении кода',
        )

    def handle(self, *args, **options):
        self.stdout.write('Запуск Telegram бота...')
        
        if options['noreload']:
            import os
            os.environ["RUN_MAIN"] = "true"
            
        asyncio.run(run_bot())


