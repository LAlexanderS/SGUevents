import uuid
import requests
import json
import os
from django.core.files.base import ContentFile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.serialization import deserialize_telegram_object_to_python
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import async_to_sync
import aiohttp
import asyncio
from django.urls import reverse


logger = logging.getLogger('my_debug_logger')


ADMIN_TG_NAME = os.getenv("ADMIN_TG_NAME")


def send_message_to_support_chat(message):
    from aiogram import Bot
    bot = Bot(token=settings.ACTIVE_TELEGRAM_BOT_TOKEN)
    support_chat_id = settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID
    try:
        async_to_sync(bot.send_message)(chat_id=support_chat_id, text=message)
        logger.info(f"Сообщение успешно отправлено в чат поддержки: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в чат поддержки: {e}")




def send_confirmation_to_user(telegram_id):
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    confirmation_message = "Ваш запрос на предоставление админских прав был отправлен администратору."
    data = {
        "chat_id": telegram_id,
        "text": confirmation_message,
    }
    response = requests.post(send_url, data=data)
    if not response.ok:
        print(f"Ошибка отправки подтверждающего сообщения пользователю: {response.text}")


def send_message_to_user(telegram_id, message, event_id=None, reply_markup=None):
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": telegram_id,
        "text": message,
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    response = requests.post(send_url, data=data)
    if response.ok:
        print(f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id}")
    else:
        print(f"Ошибка отправки сообщения пользователю: {response.text}")

def send_message_to_user(telegram_id, message, event_id=None, reply_markup=None):
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": telegram_id,
        "text": message,
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    response = requests.post(send_url, data=data)
    if response.ok:
        print(f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id}")
    else:
        print(f"Ошибка отправки сообщения пользователю: {response.text}")

def send_message_to_user_with_toggle_button(telegram_id, message, event_id, notifications_enabled, chat_url=None):
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    button_text = "\U0001F534 Отключить уведомления" if notifications_enabled else "\U0001F7E2 Включить уведомления"
    callback_data = f"toggle_{event_id}"
    inline_keyboard = {
        "inline_keyboard": [[
            {
                "text": button_text,
                "callback_data": callback_data
            }
        ]]
    }

    # Добавляем ссылку на чат участников, если передан chat_url
    if chat_url:
        inline_keyboard["inline_keyboard"].append([
            {
                "text": "\U0001F4AC Чат участников",
                "url": chat_url
            }
        ])

    data = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(inline_keyboard)
    }
    
    response = requests.post(send_url, json=data)
    if response.ok:
        logger.info(f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id}")
    else:
        logger.error(f"Ошибка отправки сообщения пользователю: {response.text}")



from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json


logger = logging.getLogger('my_debug_logger')

def send_message_to_user_with_review_buttons(telegram_id, message, event_unique_id, event_type):
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"

    # Проверяем, что event_unique_id является валидным UUID
    try:
        uuid_obj = uuid.UUID(event_unique_id)  # Проверка UUID
    except ValueError:
        logger.error(f"Некорректный UUID: {event_unique_id}")
        return

    # Создаем клавиатуру
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="\U0000270D Оставить отзыв",
                callback_data=f"review:{uuid_obj}:{event_type}"
            )
        ]
    ])

    data = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": inline_keyboard_to_dict(reply_markup)
    }

    response = requests.post(send_url, json=data)
    if response.ok:
        logger.info(f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id}")
    else:
        logger.error(f"Ошибка отправки сообщения пользователю: {response.text}")

def inline_keyboard_to_dict(inline_keyboard):
    keyboard = []
    for row in inline_keyboard.inline_keyboard:
        row_buttons = []
        for button in row:
            button_data = {
                "text": button.text,
                "callback_data": button.callback_data
            }
            row_buttons.append(button_data)
        keyboard.append(row_buttons)
    return {"inline_keyboard": keyboard}


def send_custom_notification_with_toggle(telegram_id, message, event_unique_id, notifications_enabled):
    """
    Отправка сообщения с уникальным ID мероприятия и кнопкой для включения/отключения уведомлений.

    :param telegram_id: Telegram ID пользователя
    :param message: Сообщение для отправки
    :param event_unique_id: Уникальный ID мероприятия (UUID)
    :param notifications_enabled: Состояние уведомлений (True для включенных, False для отключенных)
    """
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"

    button_text = "\U0001F534 Отключить уведомления" if notifications_enabled else "\U0001F7E2 Включить уведомления"
    callback_data = f"notify_toggle_{event_unique_id}"

    inline_keyboard = {
        "inline_keyboard": [[
            {
                "text": button_text,
                "callback_data": callback_data
            }
        ]]
    }

    data = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(inline_keyboard)
    }

    response = requests.post(send_url, data=data)
    if response.ok:
        logger.info(
            f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id} для мероприятия с ID: {event_unique_id}")
    else:
        logger.error(f"Ошибка отправки сообщения пользователю с telegram_id: {telegram_id}. Ответ: {response.text}")


def send_notification_with_toggle(telegram_id, message, event_id=None, notifications_enabled=True):
    """
    Отправляет уведомление пользователю с кнопкой включения/отключения уведомлений
    """
    try:
        send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
        
        button_text = "\U0001F534 Отключить уведомления" if notifications_enabled else "\U0001F7E2 Включить уведомления"
        
        data = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": json.dumps({
                "inline_keyboard": [[{
                    "text": button_text,
                    "callback_data": f"toggle_notifications:{event_id}:{not notifications_enabled}"
                }]]
            })
        }
        
        logger.info(f"Отправка запроса в Telegram API: URL={send_url}, data={json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(send_url, json=data)
        response_data = response.json()
        
        logger.info(f"Ответ от Telegram API: {json.dumps(response_data, ensure_ascii=False)}")
        
        if not response.ok or not response_data.get('ok'):
            logger.error(f"Ошибка при отправке сообщения в Telegram: {response_data.get('description', 'Неизвестная ошибка')}")
            return False
            
        return response_data
        
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения в Telegram: {str(e)}")
        return False

# Функция для отправки учетных данных новому пользователю
# Включает команду /start, чтобы автоматически начать взаимодействие с ботом
def send_registration_details_sync(telegram_id, username, password):
    """
    Отправляет учетные данные новому пользователю через Telegram
    """
    try:
        # Получаем базовый URL для ссылки на профиль
        webhook_host = os.getenv('WEBHOOK_HOST', '').rstrip('/')
        base_url = webhook_host if webhook_host else "https://event.larin.work"
        profile_url = f"{base_url}{reverse('users:profile')}"
        
        message = (
            f"👋 <b>Добро пожаловать!</b>\n\n"
            f"🔐 <b>Ваши учетные данные:</b>\n\n"
            f"👤 <b>Логин:</b> <code>{username}</code>\n"
            f"🔑 <b>Пароль:</b> <code>{password}</code>\n\n"
            f"💡 <b>Способы входа на портал:</b>\n"
            f"• По логину и паролю\n"
            f"• Через ваш аккаунт Telegram\n\n"
            f"⚙️ Пароль можно изменить в <a href=\"{profile_url}\">профиле пользователя</a> на портале."
        )
        
        url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': telegram_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"Учетные данные отправлены новому пользователю {username}")
        else:
            logger.error(f"Ошибка при отправке сообщения: {response.status_code}, {response.text}")
        
        # Отправляем кнопку с ссылкой на портал (используем тот же домен, что для вебхука)
        site_keyboard = {
            "inline_keyboard": [
                [{
                    "text": "🌐 Перейти на портал",
                    "url": base_url
                }]
            ]
        }
        
        site_payload = {
            'chat_id': telegram_id,
            'text': "Перейти на портал:",
            'reply_markup': json.dumps(site_keyboard)
        }
        
        requests.post(url, json=site_payload, headers=headers)
            
        # Отправляем клавиатуру меню (2x2)
        kb = [
            [
                "👤 Мой профиль",
                "📓 Мои мероприятия"
            ],
            [
                "❔ Помощь",
                "🌐 Портал"
            ]
        ]
        keyboard = {
            'keyboard': kb,
            'resize_keyboard': True,
            'one_time_keyboard': False
        }
        
        payload['text'] = "Вас приветствует Event бот СГУ"
        payload['reply_markup'] = json.dumps(keyboard)
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"Ошибка при отправке клавиатуры: {response.status_code}, {response.text}")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке учетных данных в Telegram: {e}")

# Функция для принудительного вызова команды /start для нового пользователя
async def cmd_start_user(telegram_id):
    try:
        from aiogram import Bot, Dispatcher, types
        bot = Bot(token=settings.ACTIVE_TELEGRAM_BOT_TOKEN)

        kb = [
            [
                types.KeyboardButton(text="\U0001F464 Мой профиль"),
                types.KeyboardButton(text="📓 Мои мероприятия")
            ],
            [
                types.KeyboardButton(text="\U00002754 Помощь"),
                types.KeyboardButton(text="🌐 Портал")
            ],
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите пункт меню"
        )
        await bot.send_message(chat_id=telegram_id, text="Вас приветствует Event бот СГУ", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при вызове /start для пользователя {telegram_id}: {e}")

# Функция для отправки нового пароля при его смене
def send_password_change_details_sync(telegram_id, username, new_password):
    try:
        message = (
            f"\U0001F512 Пароль для аккаунта {username} успешно изменён.\n"
            f"Если это были не вы — срочно сообщите в поддержку."
        )
        send_message_to_telegram(telegram_id, message)
        logger.info(f"Отправлено уведомление о смене пароля пользователю {username}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о смене пароля в Telegram: {e}")

# Вспомогательная функция для отправки сообщения в Telegram
def send_message_to_telegram(telegram_id, message, reply_markup=None):
    import requests
    from django.conf import settings

    url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    # Добавляем обработку reply_markup, если он передан
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.error(f"Ошибка при отправке сообщения: {response.status_code}, {response.text}")

# Функция для создания inline-клавиатуры с кнопками
def create_event_keyboard(event_id, notifications_enabled=True, include_unregister_button=False):
    """
    Создание inline клавиатуры для уведомлений о мероприятии.

    :param event_id: Идентификатор мероприятия.
    :param notifications_enabled: Состояние уведомлений (True для включенных, False для отключенных).
    :param include_unregister_button: Включать ли кнопку отмены регистрации.
    :return: Словарь с клавиатурой.
    """
    buttons = []

    # Кнопка для включения/отключения уведомлений
    button_text = "\U0001F534 Откл. уведомления" if notifications_enabled else "\U0001F7E2 Вкл. уведомления"
    callback_data = f"toggle_{event_id}"
    buttons.append({
        "text": button_text,
        "callback_data": callback_data
    })

    # Кнопка для отмены регистрации на мероприятие
    if include_unregister_button:
        unregister_callback_data = f"unregister_{event_id}"
        buttons.append({
            "text": "\U0000274C Отм. регистрацию",
            "callback_data": unregister_callback_data
        })

    # Формирование клавиатуры
    inline_keyboard = {
        "inline_keyboard": [buttons]
    }

    return inline_keyboard

# Функция для отправки уведомления с кнопкой отмены регистрации
def send_event_notification_with_buttons(telegram_id, message, event_id, notifications_enabled=True, include_unregister_button=False):
    """
    Отправка сообщения пользователю с кнопками управления уведомлениями и отменой регистрации.

    :param telegram_id: Telegram ID пользователя.
    :param message: Сообщение для отправки.
    :param event_id: Идентификатор мероприятия.
    :param notifications_enabled: Состояние уведомлений (True для включенных, False для отключенных).
    :param include_unregister_button: Включать ли кнопку отмены регистрации.
    """
    reply_markup = create_event_keyboard(event_id, notifications_enabled, include_unregister_button)
    send_message_to_telegram(telegram_id, message, reply_markup=reply_markup)

async def _send_telegram_message(chat_id: str, text: str) -> None:
    """
    Асинхронно отправляет сообщение в Telegram
    """
    bot_token = settings.ACTIVE_TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise ValueError("ACTIVE_TELEGRAM_BOT_TOKEN не установлен")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"Ошибка отправки сообщения в Telegram: {response_text}")

async def get_chat_info(chat_id: str) -> dict:
    """
    Получает информацию о чате через Telegram API
    """
    bot_token = settings.ACTIVE_TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise ValueError("ACTIVE_TELEGRAM_BOT_TOKEN не установлен")

    url = f"https://api.telegram.org/bot{bot_token}/getChat"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={'chat_id': chat_id}) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"Ошибка получения информации о чате: {response_text}")
            return await response.json()

def send_chat_id_info(chat_id: str) -> None:
    """
    Отправляет информацию об ID чата пользователю
    """
    try:
        chat_info = async_to_sync(get_chat_info)(chat_id)
        chat_data = chat_info.get('result', {})
        chat_type = chat_data.get('type', 'неизвестный')
        
        message = (
            f"ℹ️ <b>Информация о чате:</b>\n\n"
            f"ID чата: <code>{chat_id}</code>\n"
            f"Тип чата: {chat_type}\n"
        )
        
        if chat_type in ['group', 'supergroup']:
            message += f"Название: {chat_data.get('title', 'не указано')}\n"
        elif chat_type == 'private':
            username = chat_data.get('username', 'не указано')
            first_name = chat_data.get('first_name', '')
            last_name = chat_data.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            message += f"Имя: {full_name}\n"
            if username:
                message += f"Username: @{username}\n"
        
        send_message_to_telegram(chat_id, message)
    except Exception as e:
        error_message = f"❌ Ошибка при получении информации о чате: {str(e)}"
        send_message_to_telegram(chat_id, error_message)

def send_password_to_user(telegram_id: str, password: str) -> None:
    """
    Отправляет пароль пользователю через Telegram
    """
    message = (
        "🔐 <b>Ваши данные для входа на сайт:</b>\n\n"
        f"Пароль: <code>{password}</code>\n\n"
        "Пожалуйста, сохраните эти данные в надежном месте."
    )
    
    # Используем синхронную функцию отправки сообщения вместо асинхронной
    send_message_to_telegram(telegram_id, message)

def send_message_to_event_support_chat(text, support_chat_id, bot_token=None):
    """
    Отправляет сообщение в чат поддержки конкретного мероприятия
    """
    if not bot_token:
        bot_token = settings.ACTIVE_TELEGRAM_BOT_TOKEN

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chat_id = str(support_chat_id)
    if not chat_id.startswith('-'):
        chat_id = f"-{chat_id}"
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to send message to event support chat: {response.status_code}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error sending message to event support chat: {str(e)}")
        return False

def download_telegram_avatar(telegram_id):
    """
    Загрузка аватара пользователя из Telegram
    """
    try:
        # Получаем информацию о пользователе из Telegram API
        get_user_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/getUserProfilePhotos"
        params = {
            'user_id': telegram_id,
            'limit': 1
        }
        
        response = requests.get(get_user_url, params=params)
        if not response.ok:
            logger.warning(f"Не удалось получить фото профиля для пользователя {telegram_id}: {response.text}")
            return None
            
        data = response.json()
        if not data.get('result') or not data['result'].get('photos'):
            logger.info(f"У пользователя {telegram_id} нет фото профиля")
            return None
            
        # Берем самое большое фото из первого набора
        photos = data['result']['photos'][0]
        largest_photo = max(photos, key=lambda x: x['width'])
        file_id = largest_photo['file_id']
        
        # Получаем путь к файлу
        get_file_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/getFile"
        file_response = requests.get(get_file_url, params={'file_id': file_id})
        
        if not file_response.ok:
            logger.warning(f"Не удалось получить файл {file_id}: {file_response.text}")
            return None
            
        file_path = file_response.json()['result']['file_path']
        
        # Скачиваем файл
        download_url = f"https://api.telegram.org/file/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/{file_path}"
        image_response = requests.get(download_url)
        
        if not image_response.ok:
            logger.warning(f"Не удалось скачать изображение: {image_response.text}")
            return None
            
        # Создаем объект ContentFile для Django
        filename = f"telegram_avatar_{telegram_id}.jpg"
        content_file = ContentFile(image_response.content, name=filename)
        
        logger.info(f"Успешно загружен аватар для пользователя {telegram_id}")
        return content_file
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке аватара из Telegram для пользователя {telegram_id}: {str(e)}")
        return None

def get_event_url(event_obj):
    """
    Генерирует полный URL для мероприятия в зависимости от его типа
    """
    try:
        # Используем тот же домен, что для вебхука
        webhook_host = os.getenv('WEBHOOK_HOST', '').rstrip('/')
        base_url = webhook_host if webhook_host else "https://event.larin.work"
        
        # Определяем тип мероприятия и соответствующий URL
        if hasattr(event_obj, '_meta'):
            model_name = event_obj._meta.model_name
            
            if model_name == 'events_online':
                relative_url = reverse('events_available:online_card', kwargs={'event_slug': event_obj.slug})
            elif model_name == 'events_offline':
                relative_url = reverse('events_available:offline_card', kwargs={'event_slug': event_obj.slug})
            elif model_name == 'attractions':
                relative_url = reverse('events_cultural:attractions_card', kwargs={'event_slug': event_obj.slug})
            elif model_name == 'events_for_visiting':
                relative_url = reverse('events_cultural:events_for_visiting_card', kwargs={'event_slug': event_obj.slug})
            else:
                logger.warning(f"Неизвестный тип мероприятия: {model_name}")
                return None
                
            return f"{base_url}{relative_url}"
    except Exception as e:
        logger.error(f"Ошибка при генерации URL для мероприятия: {e}")
        return None

def create_event_hyperlink(event_name, event_url):
    """
    Создает HTML гиперссылку для мероприятия
    """
    if event_url:
        return f'<a href="{event_url}">{event_name}</a>'
    else:
        return event_name

def send_text_to_chat(chat_id: str, text: str, parse_html: bool = True):
    """
    Отправляет текстовое сообщение в указанный чат Telegram по chat_id.
    """
    try:
        url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': str(chat_id),
            'text': text,
        }
        if parse_html:
            payload['parse_mode'] = 'HTML'
        response = requests.post(url, json=payload)
        if not response.ok:
            logger.error(f"Ошибка отправки в чат {chat_id}: {response.status_code} {response.text}")
        return response
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения в чат {chat_id}: {e}")
        return None
