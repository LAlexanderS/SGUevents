import uuid

import requests
import json
import os

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



logger = logging.getLogger('my_debug_logger')


ADMIN_TG_NAME = os.getenv("ADMIN_TG_NAME")


def send_message_to_support_chat(message):
    from aiogram import Bot
    bot = Bot(token=settings.ACTIVE_TELEGRAM_BOT_TOKEN)
    support_chat_id = settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID
    try:
        # Получаем пользователя и проверяем статус VIP
        user_model = get_user_model()
        user = async_to_sync(user_model.objects.get)(telegram_id=message.from_user.id)
        vip_emoji = "\U0001F451 " if user.vip else ""  # Добавляем эмодзи короны, если пользователь VIP

        # Форматируем имя пользователя с иконкой
        user_name_with_emoji = f"{vip_emoji}{user.first_name} {user.last_name}"

        # Форматируем сообщение
        formatted_message = f"Новый вопрос от пользователя {user_name_with_emoji}:\n\n{message.text}"

        async_to_sync(bot.send_message)(chat_id=support_chat_id, text=formatted_message)
        logger.info(f"Сообщение успешно отправлено в чат поддержки: {formatted_message}")
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

def send_message_to_user_with_toggle_button(telegram_id, message, event_id, notifications_enabled):
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
    data = {
        "chat_id": telegram_id,
        "text": message,
        "reply_markup": json.dumps(inline_keyboard)
    }
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

def send_message_to_user_with_toggle_button(telegram_id, message, event_id, notifications_enabled):
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
    data = {
        "chat_id": telegram_id,
        "text": message,
        "reply_markup": json.dumps(inline_keyboard)
    }
    response = requests.post(send_url, data=data)
    if response.ok:
        print(f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id}")
    else:
        print(f"Ошибка отправки сообщения пользователю: {response.text}")



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
        "reply_markup": json.dumps(inline_keyboard)
    }

    response = requests.post(send_url, data=data)
    if response.ok:
        logger.info(
            f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id} для мероприятия с ID: {event_unique_id}")
    else:
        logger.error(f"Ошибка отправки сообщения пользователю с telegram_id: {telegram_id}. Ответ: {response.text}")


def send_notification_with_toggle(telegram_id, message, event_id, notifications_enabled):
    """
    Отправка сообщения пользователю с кнопкой для включения/отключения уведомлений.

    :param telegram_id: Telegram ID пользователя
    :param message: Сообщение для отправки
    :param event_id: UUID мероприятия
    :param notifications_enabled: Состояние уведомлений (True для включенных, False для отключенных)
    """
    send_url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    button_text = "\U0001F534 Отключить уведомления" if notifications_enabled else "\U0001F7E2 Включить уведомления"
    callback_data = f"notify_toggle_{event_id}"  # Используем UUID и префикс "notify_toggle_" для обработки в новом хендлере
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
        "reply_markup": json.dumps(inline_keyboard)
    }

    response = requests.post(send_url, data=data)
    if response.ok:
        print(f"Сообщение успешно отправлено пользователю с telegram_id: {telegram_id}")
    else:
        print(f"Ошибка отправки сообщения пользователю: {response.text}")

# Функция для отправки учетных данных новому пользователю
# Включает команду /start, чтобы автоматически начать взаимодействие с ботом
def send_registration_details_sync(telegram_id, username, password):
    try:
        message = (
            f"\U0001F44B Добро пожаловать!\n"
            f"Ваши учетные данные:\n"
            f"Username: {username}\nПароль: {password}\n"
            f"Вы можете войти просто через telegram, без логина и пароля"
        )
        send_message_to_telegram(telegram_id, message)
        async_to_sync(cmd_start_user)(telegram_id)  # Автоматически вызываем /start после отправки учетных данных
        logger.info(f"Учетные данные отправлены новому пользователю {username}")
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
                types.KeyboardButton(text="\U0001F5D3 Мои мероприятия"),
                types.KeyboardButton(text="\U00002754 Помощь")
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
            f"\U0001F512 Ваш пароль был успешно изменен.\n"
            f"Ваши новые учетные данные:\n"
            f"Username: {username}\nПароль: {new_password}"
        )
        send_message_to_telegram(telegram_id, message)
        logger.info(f"Новый пароль отправлен пользователю {username}")
    except Exception as e:
        logger.error(f"Ошибка при отправке нового пароля в Telegram: {e}")

# Вспомогательная функция для отправки сообщения в Telegram
def send_message_to_telegram(telegram_id, message, reply_markup=None):
    import requests
    from django.conf import settings

    url = f"https://api.telegram.org/bot{settings.ACTIVE_TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': message
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
