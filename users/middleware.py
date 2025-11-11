from threading import local
from django.conf import settings
from .miniapp_utils import get_init_data_from_request, validate_init_data

_user = local()

class CurrentUserMiddleware:
    """
    Middleware для сохранения текущего пользователя, который вносит изменения.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user
        response = self.get_response(request)
        return response

    @staticmethod
    def get_current_user():
        return getattr(_user, 'value', None)

class NoCacheMiddleware:
    """
    Middleware для отключения кэширования в режиме разработки
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if settings.DEBUG:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response

class MiniAppAuthMiddleware:
    """
    Middleware для определения запросов из Telegram Mini App.
    Устанавливает флаг request.is_miniapp если запрос пришел из Mini App.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем наличие initData
        init_data = get_init_data_from_request(request)
        
        if init_data and validate_init_data(init_data):
            request.is_miniapp = True
            request.miniapp_init_data = init_data
        else:
            request.is_miniapp = False
            request.miniapp_init_data = None
            
        response = self.get_response(request)
        return response
