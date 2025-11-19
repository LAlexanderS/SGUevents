import hmac
import hashlib
import urllib.parse
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def validate_init_data(init_data: str) -> bool:
    """
    Проверяет валидность initData от Telegram Web App API.
    
    Args:
        init_data: Строка initData от Telegram Web App
        
    Returns:
        True если данные валидны, False иначе
    """
    if not init_data:
        return False
    
    # Используем токен бота для получения секретного ключа
    bot_token = settings.ACTIVE_TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.warning("ACTIVE_TELEGRAM_BOT_TOKEN не настроен, проверка initData невозможна")
        return False
    
    try:
        # Парсим initData
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # Извлекаем hash и остальные данные
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return False
        
        # Создаем строку для проверки (все поля кроме hash, отсортированные)
        data_check_string_parts = []
        for key, value_list in parsed_data.items():
            if key != 'hash':
                data_check_string_parts.append(f"{key}={value_list[0]}")
        
        data_check_string_parts.sort()
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Вычисляем секретный ключ: HMAC-SHA-256("WebAppData", bot_token)
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем hash
        return hmac.compare_digest(calculated_hash, received_hash)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке initData: {str(e)}")
        return False


def extract_telegram_id(init_data: str) -> Optional[str]:
    """
    Извлекает telegram_id из валидного initData.
    
    Args:
        init_data: Строка initData от Telegram Web App
        
    Returns:
        telegram_id как строка или None если не удалось извлечь
    """
    if not init_data:
        return None
    
    try:
        # Парсим initData
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # Извлекаем user данные (JSON строка)
        user_data = parsed_data.get('user', [None])[0]
        if not user_data:
            return None
        
        # Парсим JSON
        import json
        user_dict = json.loads(user_data)
        
        # Извлекаем id
        telegram_id = user_dict.get('id')
        if telegram_id:
            return str(telegram_id)
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении telegram_id из initData: {str(e)}")
        return None


def get_init_data_from_request(request) -> Optional[str]:
    """
    Извлекает initData из запроса (query параметры или заголовки).
    
    Args:
        request: Django HttpRequest объект
        
    Returns:
        initData строка или None если не найдена
    """
    # Проверяем query параметры (Telegram передает initData в параметре _tgWebAppInitData)
    init_data = request.GET.get('_tgWebAppInitData') or request.GET.get('tgWebAppInitData') or request.GET.get('initData')
    if init_data:
        logger.debug(f"Найден initData в query параметрах: {init_data[:50]}...")
        return init_data
    
    # Проверяем заголовки
    init_data = request.headers.get('X-Telegram-Init-Data') or request.headers.get('X-Telegram-Web-App-Init-Data')
    if init_data:
        logger.debug(f"Найден initData в заголовках: {init_data[:50]}...")
        return init_data
    
    logger.debug("initData не найден в запросе")
    return None

