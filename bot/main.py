import asyncio
import logging
import uuid
import os

import requests
import json
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Update
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.bot import DefaultBotProperties
from aiohttp import web
from aiogram.types import Update


load_dotenv()
from bot.django_initializer import setup_django_environment

from django.contrib.auth import get_user_model
from django.conf import settings
logging.basicConfig(level=logging.INFO)

# Initialize bot
TOKEN = settings.ACTIVE_TELEGRAM_BOT_TOKEN
SUPPORT_CHAT_ID = settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID
storage = MemoryStorage()
dp = Dispatcher()
router = Router()
logger = logging.getLogger(__name__)

WEBHOOK_HOST = os.getenv('WEBHOOK_HOST') # URL вашего сервера
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')  # Уникальный путь для webhook
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


class SupportRequestForm(StatesGroup):
    waiting_for_question = State()

class ReviewForm(StatesGroup):
    waiting_for_review = State()



async def get_user_profile(telegram_id):
    User = get_user_model()
    try:
        return await sync_to_async(User.objects.get)(telegram_id=telegram_id)
    except User.DoesNotExist:
        return None

async def get_user_events(user):
    from django.utils.timezone import localtime
    from bookmarks.models import Registered
    events = await sync_to_async(list)(Registered.objects.filter(user=user))
    event_details = []
    for event in events:
        if await sync_to_async(lambda: event.online)():
            event_name = await sync_to_async(lambda: event.online.name)()
            start_datetime = await sync_to_async(lambda: event.online.start_datetime)()
        elif await sync_to_async(lambda: event.offline)():
            event_name = await sync_to_async(lambda: event.offline.name)()
            start_datetime = await sync_to_async(lambda: event.offline.start_datetime)()
        elif await sync_to_async(lambda: event.attractions)():
            event_name = await sync_to_async(lambda: event.attractions.name)()
            start_datetime = await sync_to_async(lambda: event.attractions.start_datetime)()
        elif await sync_to_async(lambda: event.for_visiting)():
            event_name = await sync_to_async(lambda: event.for_visiting.name)()
            start_datetime = await sync_to_async(lambda: event.for_visiting.start_datetime)()
        else:
            event_name = "Неизвестное мероприятие"
            start_datetime = None

        if start_datetime:
            start_datetime_local = localtime(start_datetime)
            event_details.append(f"{event_name}\n\U0001F5D3 {start_datetime_local.strftime('%d.%m.%Y %H:%M')}")
        else:
            event_details.append(event_name)

    return event_details


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
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
    await message.answer("Вас приветствует Event бот СГУ", reply_markup=keyboard)

@dp.message(F.text == "\U0001F464 Мой профиль")
async def profile(message: types.Message):
    user = await get_user_profile(message.from_user.id)
    if user:
        department_name = await sync_to_async(get_department_name)(user)
        full_name = f"{user.last_name} {user.first_name}" + (f" {user.middle_name}" if user.middle_name else "")
        response_text = f"Ваше ФИО: {full_name}\nОтдел: {department_name}"
    else:
        response_text = "Вы не зарегистрированы на портале."
    await message.answer(response_text)

def get_department_name(user):
    return user.department.department_name if user.department else "Не указан"

@dp.message(F.text == "\U0001F5D3 Мои мероприятия")
async def my_events(message: types.Message):
    user = await get_user_profile(message.from_user.id)
    if user:
        event_details = await get_user_events(user)
        if event_details:
            for event_detail in event_details:
                response_text = f"Мероприятие: {event_detail}"
                await message.answer(response_text)
        else:
            await message.answer("Вы не зарегистрированы на какие-либо мероприятия.")
    else:
        await message.answer("Вы не зарегистрированы на портале.")


@dp.message(F.text == "\U00002754 Помощь")
async def help_request(message: types.Message, state: FSMContext):
    user = await get_user_profile(message.from_user.id)
    if user:
        await message.answer("\U00002754 Пожалуйста, введите ваш вопрос:")
        await state.set_state(SupportRequestForm.waiting_for_question)
    else:
        await message.answer("Вы не зарегистрированы на портале.")

@dp.message(SupportRequestForm.waiting_for_question)
async def receive_question(message: types.Message, state: FSMContext):
    from users.models import SupportRequest
    user = await get_user_profile(message.from_user.id)
    if user:
        # Сохраняем вопрос в базе данных
        support_request = await sync_to_async(SupportRequest.objects.create)(
            user=user,
            question=message.text
        )
        # Отправляем вопрос в чат поддержки
        support_message = f"Новый вопрос от пользователя {user.username}:\n\n{message.text}"
        send_message_to_support_chat(support_message)
        await message.answer("Ваш вопрос отправлен в техподдержку. Спасибо!")
    else:
        await message.answer("Вы не зарегистрированы на портале.")
    await state.clear()
def send_message_to_support_chat(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': SUPPORT_CHAT_ID,
        'text': text
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code}, {response.text}")


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_notification(callback_query: types.CallbackQuery):
    event_id = callback_query.data.split("_")[1]
    user = await get_user_profile(callback_query.from_user.id)
    if user:
        from bookmarks.models import Registered
        registration = await sync_to_async(Registered.objects.get)(user=user, id=event_id)
        registration.notifications_enabled = not registration.notifications_enabled
        await sync_to_async(registration.save)()

        new_button_text = "\U0001F7E2 Включить уведомления" if not registration.notifications_enabled else "\U0001F534 Отключить уведомления"
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=new_button_text, callback_data=f"toggle_{event_id}")]
        ])
        await callback_query.message.edit_reply_markup(reply_markup=inline_keyboard)
        await callback_query.answer(f"Уведомления {'включены' if registration.notifications_enabled else 'отключены'}.")
    else:
        await callback_query.answer("Вы не зарегистрированы на портале.")


@router.message(ReviewForm.waiting_for_review)
async def receive_review(message: types.Message, state: FSMContext):
    from django.shortcuts import get_object_or_404
    from django.contrib.contenttypes.models import ContentType
    from events_cultural.models import Attractions, Events_for_visiting
    from events_available.models import Events_online, Events_offline
    from bookmarks.models import Review

    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer("Произошла ошибка, попробуйте снова.")
        await state.clear()
        return

    data = await state.get_data()
    event_unique_id = data.get("event_id")
    event_type = data.get("event_type")

    comment = message.text

    if not comment:
        await message.answer("Комментарий не может быть пустым")
        return

    model_map = {
        "online": Events_online,
        "offline": Events_offline,
        "attractions": Attractions,
        "for_visiting": Events_for_visiting
    }

    model = model_map.get(event_type)
    if not model:
        await message.answer("Некорректный тип мероприятия")
        return

    try:
        event = await sync_to_async(get_object_or_404)(model, unique_id=event_unique_id)
        content_type = await sync_to_async(ContentType.objects.get_for_model)(model)
        review = await sync_to_async(Review.objects.create)(
            user=user,
            content_type=content_type,
            object_id=event.id,  # Используем внутренний ID для создания отзыва
            comment=comment
        )

        await message.answer("Спасибо за ваш отзыв!")
    except model.DoesNotExist:
        await message.answer("Не удалось найти событие. Возможно, оно было удалено.")
    except ValueError:
        await message.answer("Некорректный UUID для события.")
    finally:
        await state.clear()

@router.callback_query(F.data.startswith("review:"))
async def handle_leave_review(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        _, event_unique_id, event_type = callback_query.data.split(":")

        # Проверяем, что event_unique_id является валидным UUID
        try:
            uuid_obj = uuid.UUID(event_unique_id)
        except ValueError:
            await callback_query.answer("Некорректный UUID для события.")
            return

        user = await get_user_profile(callback_query.from_user.id)
        if user:
            await callback_query.message.answer("Пожалуйста, напишите ваш отзыв:")
            await state.set_state(ReviewForm.waiting_for_review)
            await state.update_data(event_id=str(uuid_obj), event_type=event_type)
        else:
            await callback_query.answer("Вы не зарегистрированы на портале.")
    except Exception as e:
        await callback_query.answer(f"Произошла ошибка: {e}")


@router.callback_query(F.data.startswith("notify_toggle_"))
async def toggle_event_notification(callback_query: types.CallbackQuery):
    event_unique_id = callback_query.data.split("_")[2]
    user = await get_user_profile(callback_query.from_user.id)

    if user:
        from bookmarks.models import Registered
        registration = None

        # Попробуем найти регистрацию по каждому типу события
        try:
            registration = await sync_to_async(Registered.objects.get)(
                user=user, online__unique_id=event_unique_id
            )
        except Registered.DoesNotExist:
            try:
                registration = await sync_to_async(Registered.objects.get)(
                    user=user, offline__unique_id=event_unique_id
                )
            except Registered.DoesNotExist:
                try:
                    registration = await sync_to_async(Registered.objects.get)(
                        user=user, attractions__unique_id=event_unique_id
                    )
                except Registered.DoesNotExist:
                    try:
                        registration = await sync_to_async(Registered.objects.get)(
                            user=user, for_visiting__unique_id=event_unique_id
                        )
                    except Registered.DoesNotExist:
                        await callback_query.answer("Событие не найдено.")
                        return

        # Переключаем состояние уведомлений
        registration.notifications_enabled = not registration.notifications_enabled
        await sync_to_async(registration.save)()

        # Обновляем текст кнопки и отправляем новое сообщение
        new_button_text = "\U0001F7E2 Включить уведомления" if not registration.notifications_enabled else "\U0001F534 Отключить уведомления"
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=new_button_text, callback_data=f"notify_toggle_{event_unique_id}")]
        ])
        await callback_query.message.edit_reply_markup(reply_markup=inline_keyboard)
        await callback_query.answer(f"Уведомления {'включены' if registration.notifications_enabled else 'отключены'}.")
    else:
        await callback_query.answer("Вы не зарегистрированы на портале.")

# Добавляем обработчик для Webhook
async def handle_webhook(request):
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)  # Преобразуем тело запроса в JSON
        update = Update(**data)  # Создаем объект Update напрямую
        bot = Bot(token=TOKEN)  # Создаем объект бота
        await dp.feed_update(bot, update)  # Обрабатываем обновление через диспетчер
        return JsonResponse({"status": "ok"})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
# Функция запуска бота с поддержкой Webhook

async def run_bot():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Настраиваем роутер aiohttp для Webhook
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    async with bot:
        dp.include_router(router)
        
        # Устанавливаем Webhook
        await bot.set_webhook(WEBHOOK_URL)
        # Запускаем aiohttp сервер для приема запросов Webhook
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8443)  # Пример порта 8443 для HTTPS
        await site.start()
        # Запускаем бота
        try:
            await asyncio.Event().wait()  # Ожидаем остановку
        finally:
            await bot.delete_webhook()
            await runner.cleanup()


if __name__ == "__main__":
    setup_django_environment()
    asyncio.run(run_bot())