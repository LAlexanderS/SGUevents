from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class EventsAvailableConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'events_available'
	verbose_name = 'Доступные мероприятия'
	
	def ready(self):
		# сигналы чек-листа подключены в users.signals
		logger.info('EventsAvailableConfig.ready')
    
