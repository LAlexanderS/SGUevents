import asyncio
import json
import logging
import os
import uuid
import os.path

import requests
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ChatMemberUpdatedFilter, Command
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ChatMemberUpdated
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Update
from aiohttp import web
from asgiref.sync import sync_to_async
from dotenv import load_dotenv

load_dotenv()
from bot.django_initializer import setup_django_environment

from django.contrib.auth import get_user_model
from django.conf import settings
from users.models import Department

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем бота и диспетчера глобально
TOKEN = settings.ACTIVE_TELEGRAM_BOT_TOKEN
SUPPORT_CHAT_ID = settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Настройки вебхука
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '').rstrip('/')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logger.info(f"Настройки вебхука: HOST={WEBHOOK_HOST}, PATH={WEBHOOK_PATH}, URL={WEBHOOK_URL}")

# В начале файла после импортов
# print(f"Loading settings: DJANGO_ENV={settings.DJANGO_ENV}")
# print(f"DEV_SUPPORT_CHAT_ID={settings.DEV_SUPPORT_CHAT_ID}")
# print(f"SUPPORT_CHAT_ID={settings.SUPPORT_CHAT_ID}")
# print(f"ACTIVE_TELEGRAM_SUPPORT_CHAT_ID={settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID}")

class SupportRequestForm(StatesGroup):
    waiting_for_question = State()

class ReviewForm(StatesGroup):
    waiting_for_review = State()

class RegistrationForm(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_department_code = State()

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
        event_name = None
        start_datetime = None
        
        # Используем лямбды для корректной работы с async/await
        if await sync_to_async(lambda e: bool(e.online))(event):
            event_name = await sync_to_async(lambda e: e.online.name)(event)
            start_datetime = await sync_to_async(lambda e: e.online.start_datetime)(event)
        elif await sync_to_async(lambda e: bool(e.offline))(event):
            event_name = await sync_to_async(lambda e: e.offline.name)(event)
            start_datetime = await sync_to_async(lambda e: e.offline.start_datetime)(event)
        elif await sync_to_async(lambda e: bool(e.attractions))(event):
            event_name = await sync_to_async(lambda e: e.attractions.name)(event)
            start_datetime = await sync_to_async(lambda e: e.attractions.start_datetime)(event)
        elif await sync_to_async(lambda e: bool(e.for_visiting))(event):
            event_name = await sync_to_async(lambda e: e.for_visiting.name)(event)
            start_datetime = await sync_to_async(lambda e: e.for_visiting.start_datetime)(event)
        
        if event_name:
            if start_datetime:
                start_datetime_local = localtime(start_datetime)
                event_details.append(f"{event_name}\n\U0001F5D3 {start_datetime_local.strftime('%d.%m.%Y %H:%M')}")
            else:
                event_details.append(event_name)

    return event_details

# Используем router для всех обработчиков
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        kb = [
            [
                types.KeyboardButton(text="\U0001F464 Мой профиль"),
                types.KeyboardButton(text="📓 Мои мероприятия"),
                types.KeyboardButton(text="\U00002754 Помощь")
            ],
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите пункт меню"
        )
        await message.answer("Вас приветствует Event бот СГУ", reply_markup=keyboard)
    else:
        await message.answer("Добрый день! Рад приветствовать вас! Я - персональный помощник по Платформе мероприятий. Давайте познакомимся! Как вас зовут (введите полное ФИО)?")
        await state.set_state(RegistrationForm.waiting_for_full_name)

@router.message(RegistrationForm.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    # Разбиваем ФИО на части
    full_name_parts = message.text.strip().split()
    if len(full_name_parts) < 2:
        await message.answer("Пожалуйста, введите полное ФИО (минимум фамилию и имя)")
        return
    
    # Сохраняем данные в состоянии
    await state.update_data(
        last_name=full_name_parts[0],
        first_name=full_name_parts[1],
        middle_name=full_name_parts[2] if len(full_name_parts) > 2 else None
    )
    
    await message.answer("Замечательно! Введите ваш персональный код подключения")
    await state.set_state(RegistrationForm.waiting_for_department_code)

@router.message(RegistrationForm.waiting_for_department_code)
async def process_department_code(message: types.Message, state: FSMContext):
    department_code = message.text.strip()
    
    # Получаем сохраненные данные
    user_data = await state.get_data()
    
    try:
        # Проверяем существование отдела
        department = await sync_to_async(Department.objects.get)(department_id=department_code)
        
        # Создаем токен авторизации
        from users.models import TelegramAuthToken
        auth_token = await sync_to_async(TelegramAuthToken.objects.create)(
            telegram_id=str(message.from_user.id),
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            middle_name=user_data.get('middle_name', ''),
            department_id=department_code
        )
        
        # Очищаем состояние
        await state.clear()
        
        # Формируем URL с токеном авторизации
        base_url = "https://sguevents.ru" if os.getenv('DJANGO_ENV') == 'production' else "https://sguevents.help"
        auth_url = f"{base_url}/users/auth/telegram/{auth_token.token}"
        
        # Создаем клавиатуру с кнопкой
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Завершить регистрацию",
                    url=auth_url
                )]
            ]
        )
        
        await message.answer(
            "Для завершения регистрации нажмите на кнопку ниже:",
            reply_markup=keyboard
        )
        
    except Department.DoesNotExist:
        await message.answer("Указанный код подразделения не найден. Пожалуйста, проверьте код и попробуйте снова.")
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        await message.answer("Произошла ошибка при регистрации. Пожалуйста, попробуйте позже или обратитесь в поддержку.")

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=True))
async def handle_new_member(event: ChatMemberUpdated):
    # Логика для приветствия нового пользователя
    await bot.send_message(event.chat.id, f"Добро пожаловать, {event.from_user.first_name}!")

@router.message(F.text == "\U0001F464 Мой профиль")
async def profile(message: types.Message):
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
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

@router.message(F.text == "📓 Мои мероприятия")
async def my_events(message: types.Message):
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        event_details = await get_user_events(user)
        if event_details:
            response_text = "Ваши мероприятия:\n\n"
            for i, event_detail in enumerate(event_details, 1):
                response_text += f"{i}. {event_detail}\n\n"
            await message.answer(response_text)
        else:
            await message.answer("Вы не зарегистрированы на какие-либо мероприятия.")
    else:
        await message.answer("Вы не зарегистрированы на портале.")

@router.message(F.text == "\U00002754 Помощь")
async def help_request(message: types.Message, state: FSMContext):
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        await message.answer("\U00002754 Пожалуйста, введите ваш вопрос:")
        await state.set_state(SupportRequestForm.waiting_for_question)
    else:
        await message.answer("Вы не зарегистрированы на портале.")

@router.message(Command("getid"))
async def get_chat_id(message: types.Message):
    # Проверяем, что это групповой чат
    if message.chat.type == 'private':
        await message.answer("Эта команда работает только в групповых чатах")
        return

    # Проверяем тип чата
    chat_info = await bot.get_chat(message.chat.id)
    if chat_info.type == 'group' or chat_info.type == 'supergroup':
        await message.answer(f"ID этого чата: {message.chat.id}")
    else:
        await message.answer("Эта команда работает только в групповых чатах")

# В обработчике бота
@router.message(SupportRequestForm.waiting_for_question)
async def receive_question(message: types.Message, state: FSMContext):
    from users.models import SupportRequest
    user = await get_user_profile(message.from_user.id)
    if user:
        # Сохраняем вопрос в базе данных
        support_request = await sync_to_async(SupportRequest.objects.create)(
            user=user,
            question=message.text
        )

        # Формируем сообщение с проверкой VIP статуса и HTML разметкой
        vip_emoji = "\U0001F451 " if user.vip else ""
        user_link = f'<a href="tg://user?id={user.telegram_id}">{user.first_name} {user.last_name}</a>'
        support_message = f"Новый вопрос от пользователя {vip_emoji}{user_link}:\n\n<pre>{message.text}</pre>"

        # Отправляем сообщение в чат поддержки
        send_message_to_support_chat(support_message)
        await message.answer("Ваш вопрос отправлен в техподдержку. Спасибо!")
    else:
        await message.answer("Вы не зарегистрированы на портале.")
    await state.clear()


def send_message_to_support_chat(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    chat_id = str(SUPPORT_CHAT_ID)
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
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to send message to support chat: {response.status_code}")

# Обработчики callback_query
@router.callback_query(F.data.startswith("toggle_"))
async def toggle_notification(callback_query: types.CallbackQuery):
    try:
        logger.info(f"Получен callback_query: {callback_query.data}")
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
    except Exception as e:
        logger.error(f"Ошибка в обработчике toggle_notification: {e}")
        await callback_query.answer("Произошла ошибка.")

@router.message(ReviewForm.waiting_for_review)
async def receive_review(message: types.Message, state: FSMContext):
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в обработчике receive_review: {e}")
        await message.answer("Произошла ошибка при приёме отзыва.")
        await state.clear()


@router.callback_query(F.data.startswith("review:"))
async def handle_leave_review(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Получен callback_query: {callback_query.data}")
        _, event_unique_id, event_type = callback_query.data.split(":")

        # Проверяем, что event_unique_id является валидным UUID
        try:
            uuid_obj = uuid.UUID(event_unique_id)
        except ValueError:
            await callback_query.answer("Некорректный UUID для события.")
            return

        user = await get_user_profile(callback_query.from_user.id)
        if user:
            # Создаем клавиатуру с кнопкой "Отмена"
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="\U0000274C Отмена",
                        callback_data=f"cancel_review:{uuid_obj}"
                    )
                ]
            ])

            # Отправляем сообщение с запросом на отзыв
            await callback_query.message.edit_text(
                "Пожалуйста, оставьте отзыв, или отмените запрос.",
                reply_markup=reply_markup
            )
            await state.set_state(ReviewForm.waiting_for_review)
            await state.update_data(event_id=str(uuid_obj), event_type=event_type)
        else:
            await callback_query.answer("Вы не зарегистрированы на портале.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_leave_review: {e}")
        await callback_query.answer(f"Произошла ошибка: {e}")



@router.callback_query(F.data.startswith("cancel_review:"))
async def handle_cancel_review(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Получен callback_query: {callback_query.data}")
        _, event_unique_id = callback_query.data.split(":")

        # Проверяем, что event_unique_id является валидным UUID
        try:
            uuid.UUID(event_unique_id)
        except ValueError:
            await callback_query.answer("Некорректный UUID для события.")
            return

        # Удаляем сообщение с запросом на отзыв и сбрасываем состояние
        await callback_query.message.delete()
        await state.clear()
        await callback_query.answer("Запрос на отзыв отменен.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике handle_cancel_review: {e}")
        await callback_query.answer("Произошла ошибка при отмене.")



@router.callback_query(F.data.startswith("notify_toggle_"))
async def toggle_event_notification(callback_query: types.CallbackQuery):
    try:
        logger.info(f"Получен callback_query: {callback_query.data}")
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
            new_button_text = "\U0001F7E2 Вкл. уведомления" if not registration.notifications_enabled else "\U0001F534 Откл. уведомления"
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=new_button_text, callback_data=f"notify_toggle_{event_unique_id}")]
            ])
            await callback_query.message.edit_reply_markup(reply_markup=inline_keyboard)
            await callback_query.answer(f"Уведомления {'включены' if registration.notifications_enabled else 'отключены'}.")
        else:
            await callback_query.answer("Вы не зарегистрированы на портале.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике toggle_event_notification: {e}")
        await callback_query.answer("Произошла ошибка.")

# Обработчик callback_query для отмены регистрации
@router.callback_query(F.data.startswith("unregister_"))
async def unregister_event(callback_query: types.CallbackQuery):
    from bookmarks.models import Registered
    try:
        event_id = int(callback_query.data.split('_')[1])
        user_id = callback_query.from_user.id

        # Найдите регистрацию пользователя на мероприятие
        registration = await sync_to_async(Registered.objects.get)(user__telegram_id=user_id, id=event_id)
        await sync_to_async(registration.delete)()

        await callback_query.answer("Вы успешно отменили регистрацию на мероприятие.")
        await callback_query.message.edit_text("Вы отменили регистрацию на мероприятие.")
    except Registered.DoesNotExist:
        await callback_query.answer("Не удалось найти вашу регистрацию.")
    except Exception as e:
        logger.error(f"Ошибка при отмене регистрации: {e}")
        await callback_query.answer("Произошла ошибка при отмене регистрации.")

async def handle_webhook(request):
    """
    Обработчик вебхука
    """
    try:
        data = await request.json()
        logger.info(f"Получены данные вебхука: {json.dumps(data)}")
        
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
        
        return web.Response(status=200, text='OK')
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return web.Response(status=500)

async def run_bot():
    """
    Запуск бота с поддержкой вебхуков
    """
    # Настраиваем приложение aiohttp
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    
    # Устанавливаем вебхук
    webhook_info = await bot.get_webhook_info()
    current_url = webhook_info.url
    logger.info(f"Текущий URL вебхука: {current_url}")
    
    if current_url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Вебхук успешно установлен на {WEBHOOK_URL}")

    # Запускаем сервер aiohttp
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8443)
    await site.start()

    logger.info("Бот запущен и слушает вебхуки на порту 8443")

    # Держим бота запущенным
    try:
        await asyncio.Event().wait()
    finally:
        await bot.delete_webhook()
        await runner.cleanup()

if __name__ == "__main__":
    setup_django_environment()
    asyncio.run(run_bot())
