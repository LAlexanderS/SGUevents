import asyncio
import json
import logging
import os
import uuid
import os.path
import yadisk
from datetime import datetime, date, timedelta
from django.utils import timezone

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
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем путь к корневой директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()
from bot.django_initializer import setup_django_environment

from django.contrib.auth import get_user_model
from django.conf import settings
# from users.models import Department

# Инициализируем бота и диспетчера глобально
TOKEN = settings.ACTIVE_TELEGRAM_BOT_TOKEN
SUPPORT_CHAT_ID = settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID

# Инициализируем переменные Яндекс.Диска глобально
YANDEX_DISK_CLIENT_ID = settings.YANDEX_DISK_CLIENT_ID
YANDEX_DISK_CLIENT_SECRET = settings.YANDEX_DISK_CLIENT_SECRET
YANDEX_DISK_OAUTH_TOKEN = settings.YANDEX_DISK_OAUTH_TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Добавляем команды в список команд бота
BOT_COMMANDS = [
    types.BotCommand(command="help", description="Задать вопрос в поддержку")
]

async def setup_bot_commands():
    """
    Установка команд бота только для чатов пользователей мероприятий с настроенной техподдержкой
    """
    from events_available.models import Events_offline
    
    try:
        # Получаем все мероприятия с настроенной техподдержкой
        events = await sync_to_async(list)(Events_offline.objects.filter(
            support_chat_id__isnull=False,
            users_chat_id__isnull=False
        ))
        
        # Для каждого мероприятия устанавливаем команды только в чате пользователей
        for event in events:
            try:
                # Устанавливаем команды в чате пользователей
                await bot.set_my_commands(
                    commands=BOT_COMMANDS,
                    scope=types.BotCommandScopeChat(chat_id=int(event.users_chat_id))
                )
                
                # Удаляем команды из чата поддержки
                await bot.delete_my_commands(
                    scope=types.BotCommandScopeChat(chat_id=int(event.support_chat_id))
                )
                
            except Exception as e:
                logger.error(f"❌ Ошибка при установке команд для чата {event.users_chat_id}: {e}")
                
        # Удаляем команды из всех остальных чатов
        try:
            # Получаем все чаты, где бот установил команды
            bot_commands = await bot.get_my_commands()
            if bot_commands:
                # Удаляем команды глобально
                await bot.delete_my_commands()
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении команд из остальных чатов: {e}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при установке команд бота: {e}")

# Настройки вебхука
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '').rstrip('/')
WEBHOOK_PATH = '/webhook/'  # Добавляем trailing slash
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logger.info(f"Настройки вебхука: HOST={WEBHOOK_HOST}, PATH={WEBHOOK_PATH}, URL={WEBHOOK_URL}")

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

async def cancel_support_request_handler(message_or_callback, state: FSMContext, is_callback=False):
    """
    Обрабатывает отмену запроса в техподдержку и возвращает пользователя в главное меню.
    
    Args:
        message_or_callback: объект Message или CallbackQuery
        state: FSMContext для очистки состояния
        is_callback: True, если это callback_query, False если message
    """
    # Очищаем состояние
    await state.clear()
    
    # Формируем сообщение об отмене
    cancel_text = (
        "❌ <b>Запрос отменён</b>\n\n"
        "Вы вернулись в главное меню. Если у вас возникнут вопросы, "
        "вы всегда можете обратиться в техподдержку через кнопку «Помощь»."
    )
    
    # Создаем главное меню
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
    
    if is_callback:
        try:
            await message_or_callback.message.edit_text(cancel_text, parse_mode='HTML')
            await message_or_callback.message.answer(
                "Главное меню:",
                reply_markup=keyboard
            )
            await message_or_callback.answer("Запрос отменён")
        except Exception:
            await message_or_callback.message.answer(cancel_text, reply_markup=keyboard, parse_mode='HTML')
            await message_or_callback.answer("Запрос отменён")
    else:
        await message_or_callback.answer(cancel_text, reply_markup=keyboard, parse_mode='HTML')

async def send_not_registered_message(message_or_callback, is_callback=False):
    """
    Отправляет расширенное сообщение о том, что пользователь не зарегистрирован,
    с кнопкой перехода на портал.
    
    Args:
        message_or_callback: объект Message или CallbackQuery
        is_callback: True, если это callback_query, False если message
    """
    # Формируем URL портала
    base_url = WEBHOOK_HOST.rstrip('/') if WEBHOOK_HOST else "https://event.larin.work"
    portal_url = f"{base_url}/"
    
    # Текст сообщения
    text = (
        "❌ Вы не зарегистрированы на портале.\n\n"
        "📋 <b>Что даёт регистрация:</b>\n"
        "• Доступ к порталу мероприятий\n"
        "• Регистрация на мероприятия\n"
        "• Просмотр ваших задач и логистики\n"
        "• Получение поддержки по мероприятиям\n\n"
        "🌐 Нажмите кнопку ниже, чтобы открыть портал и зарегистрироваться."
    )
    
    # Создаем клавиатуру с кнопкой
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🌐 Открыть портал",
                web_app=types.WebAppInfo(url=portal_url)
            )]
        ]
    )
    
    if is_callback:
        # Для callback_query используем answer с show_alert или отправляем новое сообщение
        try:
            await message_or_callback.message.answer(text, reply_markup=keyboard, parse_mode='HTML')
            await message_or_callback.answer()
        except Exception:
            await message_or_callback.answer("Вы не зарегистрированы на портале. Откройте портал через меню.", show_alert=True)
    else:
        # Для обычного сообщения
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode='HTML')

async def get_user_events(user):
    from django.utils.timezone import localtime
    from bookmarks.models import Registered
    from events_available.models import EventLogistics
    
    events = await sync_to_async(list)(Registered.objects.filter(user=user))
    event_details = []
    
    for event in events:
        event_name = None
        start_datetime = None
        event_obj = None
        event_type = None
        
        # Используем лямбды для корректной работы с async/await
        if await sync_to_async(lambda e: bool(e.online))(event):
            event_name = await sync_to_async(lambda e: e.online.name)(event)
            start_datetime = await sync_to_async(lambda e: e.online.start_datetime)(event)
            event_obj = await sync_to_async(lambda e: e.online)(event)
            event_type = 'online'
        elif await sync_to_async(lambda e: bool(e.offline))(event):
            event_name = await sync_to_async(lambda e: e.offline.name)(event)
            start_datetime = await sync_to_async(lambda e: e.offline.start_datetime)(event)
            event_obj = await sync_to_async(lambda e: e.offline)(event)
            event_type = 'offline'
        elif await sync_to_async(lambda e: bool(e.attractions))(event):
            event_name = await sync_to_async(lambda e: e.attractions.name)(event)
            start_datetime = await sync_to_async(lambda e: e.attractions.start_datetime)(event)
            event_obj = await sync_to_async(lambda e: e.attractions)(event)
            event_type = 'attractions'
        elif await sync_to_async(lambda e: bool(e.for_visiting))(event):
            event_name = await sync_to_async(lambda e: e.for_visiting.name)(event)
            start_datetime = await sync_to_async(lambda e: e.for_visiting.start_datetime)(event)
            event_obj = await sync_to_async(lambda e: e.for_visiting)(event)
            event_type = 'for_visiting'
        
        if event_name and event_obj:
            # Проверяем, есть ли логистика для этого пользователя и офлайн мероприятия
            has_logistics = False
            if event_type == 'offline':
                has_logistics = await sync_to_async(
                    lambda: EventLogistics.objects.filter(user=user, event=event_obj).exists()
                )()
            
            event_info = {
                'name': event_name,
                'start_datetime': start_datetime,
                'event_id': event_obj.id if event_obj else None,
                'event_type': event_type,
                'has_logistics': has_logistics
            }
            event_details.append(event_info)

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
        middle_name=full_name_parts[2] if len(full_name_parts) > 2 else ""
    )
    
    # Продолжаем регистрацию независимо от количества слов (минимум 2)
    await message.answer("Замечательно! Введите ваш персональный код подключения")
    await state.set_state(RegistrationForm.waiting_for_department_code)

@router.message(RegistrationForm.waiting_for_department_code)
async def process_department_code(message: types.Message, state: FSMContext):
    from users.models import Department
    department_code = message.text.strip()
    
    # Получаем сохраненные данные
    user_data = await state.get_data()
    
    try:
        # Проверяем существование отдела
        department = await sync_to_async(Department.objects.get)(department_id=department_code)
        
        # Генерируем пароль ДО создания токена
        from django.utils.crypto import get_random_string
        password = get_random_string(8)
        
        # Создаем токен авторизации с паролем и данными пользователя
        from users.models import TelegramAuthToken
        auth_token = await sync_to_async(TelegramAuthToken.objects.create)(
            telegram_id=str(message.from_user.id),
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            middle_name=user_data.get('middle_name', ''),
            department_id=department_code,
            password=password
        )
        
        # Очищаем состояние формы
        await state.clear()
        
        # Формируем URL с токеном авторизации (используем тот же домен, что для вебхука)
        base_url = WEBHOOK_HOST.rstrip('/') if WEBHOOK_HOST else "https://event.larin.work"
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
            "Нажми, чтобы завершить регистрацию. После перехода мы пришлём логин и пароль.",
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
    from users.models import Department
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        department_name = await sync_to_async(get_department_name)(user)
        full_name = f"{user.last_name} {user.first_name}" + (f" {user.middle_name}" if user.middle_name else "")
        response_text = f"Ваше ФИО: {full_name}\nОтдел: {department_name}"

        # Добавляем кнопку "Мои задачи (N)", если есть активные задачи
        from events_available.models import EventOfflineCheckList
        tasks_count = await sync_to_async(lambda: EventOfflineCheckList.objects.filter(responsible=user, completed=False).count())()
        reply_markup = None
        if tasks_count > 0:
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"📝 Мои задачи ({tasks_count})", callback_data="mytasks")]])
            reply_markup = kb
        await message.answer(response_text, reply_markup=reply_markup)
    else:
        await send_not_registered_message(message, is_callback=False)

def get_department_name(user):
    from users.models import Department
    return user.department.department_name if user.department else "Не указан"

@router.message(F.text == "📓 Мои мероприятия")
async def my_events(message: types.Message):
    from django.utils.timezone import localtime
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        event_details = await get_user_events(user)
        if event_details:
            # Сортируем мероприятия по дате (сначала ближайшие будущие, потом прошедшие)
            today = timezone.localdate()
            tomorrow = today + timedelta(days=1)
            
            def get_event_date(event_info):
                """Возвращает дату события для сортировки"""
                if event_info['start_datetime']:
                    return localtime(event_info['start_datetime']).date()
                return date.max  # События без даты в конец
            
            def get_event_group(event_info):
                """Определяет группу события для метки"""
                if not event_info['start_datetime']:
                    return "⚪ Будущее"
                event_date = localtime(event_info['start_datetime']).date()
                if event_date < today:
                    return "⚫ Прошедшее"
                elif event_date == today:
                    return "🟢 Сегодня"
                elif event_date == tomorrow:
                    return "🟡 Завтра"
                else:
                    return "⚪ Будущее"
            
            # Сортируем: сначала будущие (по возрастанию даты), потом прошедшие (по убыванию)
            future_events = [e for e in event_details if e['start_datetime'] and localtime(e['start_datetime']).date() >= today]
            past_events = [e for e in event_details if not e['start_datetime'] or localtime(e['start_datetime']).date() < today]
            
            future_events.sort(key=get_event_date)
            past_events.sort(key=get_event_date, reverse=True)
            
            sorted_event_details = future_events + past_events
            
            await message.answer("📓 Ваши мероприятия:")
            
            for event_info in sorted_event_details:
                from users.telegram_utils import get_event_url, create_event_hyperlink
                
                # Получаем объект мероприятия для создания URL
                event_obj = None
                if event_info['event_type'] == 'online':
                    from events_available.models import Events_online
                    try:
                        event_obj = await sync_to_async(Events_online.objects.get)(id=event_info['event_id'])
                    except Events_online.DoesNotExist:
                        pass
                elif event_info['event_type'] == 'offline':
                    from events_available.models import Events_offline
                    try:
                        event_obj = await sync_to_async(Events_offline.objects.get)(id=event_info['event_id'])
                    except Events_offline.DoesNotExist:
                        pass
                elif event_info['event_type'] == 'attractions':
                    from events_cultural.models import Attractions
                    try:
                        event_obj = await sync_to_async(Attractions.objects.get)(id=event_info['event_id'])
                    except Attractions.DoesNotExist:
                        pass
                elif event_info['event_type'] == 'for_visiting':
                    from events_cultural.models import Events_for_visiting
                    try:
                        event_obj = await sync_to_async(Events_for_visiting.objects.get)(id=event_info['event_id'])
                    except Events_for_visiting.DoesNotExist:
                        pass
                
                # Создаем гиперссылку для мероприятия
                event_url = await sync_to_async(get_event_url)(event_obj) if event_obj else None
                event_hyperlink = await sync_to_async(create_event_hyperlink)(event_info['name'], event_url)
                
                # Определяем группу события для метки
                event_group = get_event_group(event_info)
                
                # Формируем текст мероприятия с гиперссылкой и меткой группы
                event_text = f"{event_group}\n🎯 <b>{event_hyperlink}</b>\n"
                if event_info['start_datetime']:
                    start_datetime_local = localtime(event_info['start_datetime'])
                    event_text += f"🕐 {start_datetime_local.strftime('%d.%m.%Y %H:%M')}"
                
                # Создаем inline кнопки
                buttons = []
                
                # Если есть логистика, добавляем кнопку
                if event_info['has_logistics']:
                    buttons.append([
                        InlineKeyboardButton(
                            text="✈️ Логистика", 
                            callback_data=f"logistics_{event_info['event_id']}"
                        )
                    ])
                
                # Кнопка "Чат участников" только для online/offline при наличии id и ссылки
                if event_info['event_type'] in ('online', 'offline') and event_obj and getattr(event_obj, 'users_chat_id', None) and getattr(event_obj, 'users_chat_link', None):
                    buttons.append([
                        InlineKeyboardButton(
                            text="💬 Чат участников",
                            url=event_obj.users_chat_link
                        )
                    ])
                
                # Создаем клавиатуру
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
                
                # Отправляем сообщение
                await message.answer(
                    event_text, 
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        else:
            await message.answer("Вы не зарегистрированы на какие-либо мероприятия.")
    else:
        await send_not_registered_message(message, is_callback=False)

@router.message(Command("help"))
async def help_request(message: types.Message, state: FSMContext):
    # Проверяем, что это групповой чат
    if message.chat.type == 'private':
        return  # Просто игнорируем команду в личных чатах
        
    user = await get_user_profile(message.from_user.id)
    if not user:
        await send_not_registered_message(message, is_callback=False)
        return

    # Проверяем, является ли чат чатом поддержки для любого мероприятия
    from events_available.models import Events_offline
    try:
        # Проверяем, является ли текущий чат чатом поддержки
        is_support_chat = await sync_to_async(lambda: Events_offline.objects.filter(support_chat_id=str(message.chat.id)).exists())()
        if is_support_chat:
            # Игнорируем команду в чате поддержки
            return
            
        # Ищем мероприятие, где текущий чат - это чат пользователей
        event = await sync_to_async(Events_offline.objects.get)(users_chat_id=str(message.chat.id))
        if not event.support_chat_id:
            # Игнорируем команду, если нет чата поддержки
            return
            
    except Events_offline.DoesNotExist:
        # Игнорируем команду, если чат не привязан к мероприятию
        return

    # Получаем текст после команды /help
    command_args = message.text.split(maxsplit=1)
    if len(command_args) > 1:
        # Если есть текст после команды, отправляем его как вопрос
        question = command_args[1]
        from users.models import SupportRequest
        
        try:
            # Сохраняем вопрос в базе данных
            support_request = await sync_to_async(SupportRequest.objects.create)(
                user=user,
                question=question
            )

            # Формируем сообщение с проверкой VIP статуса и HTML разметкой
            vip_emoji = "\U0001F451 " if user.vip else ""
            user_link = f'<a href="tg://user?id={user.telegram_id}">{user.first_name} {user.last_name}</a>'
            support_message = f"Новый вопрос по мероприятию \"{event.name}\" от {vip_emoji}{user_link}:\n\n<pre>{question}</pre>"

            # Отправляем сообщение в чат поддержки мероприятия
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                'chat_id': str(event.support_chat_id),
                'text': support_message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                await message.answer("✅ Ваш вопрос отправлен в техподдержку. Спасибо!")
                logger.info(f"Вопрос успешно отправлен в поддержку мероприятия: {question}")
            else:
                await message.answer("❌ Произошла ошибка при отправке вопроса. Попробуйте позже.")
                logger.error(f"Ошибка отправки в поддержку: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке вопроса: {e}")
            await message.answer("❌ Произошла ошибка при обработке вопроса. Попробуйте позже.")
    else:
        # Если команда отправлена без текста, отправляем инструкцию
        instruction = (
            "ℹ️ Для отправки вопроса в техподдержку используйте команду /help следующим образом:\n\n"
            "<code>/help ваш вопрос</code>\n\n"
            "Например:\n"
            "<code>/help как отменить регистрацию на мероприятие?</code>\n\n"
            "❗️ Пожалуйста, пишите вопрос сразу после команды /help"
        )
        await message.answer(instruction)

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
@router.callback_query(F.data == "cancel_support_request")
async def cancel_support_request_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Назад' для отмены запроса в техподдержку"""
    await cancel_support_request_handler(callback_query, state, is_callback=True)

@router.message(SupportRequestForm.waiting_for_question)
async def receive_question(message: types.Message, state: FSMContext):
    # Проверяем, не хочет ли пользователь отменить запрос
    if message.text.lower() in ['назад', 'отмена', 'отменить', 'cancel', '⬅️ назад']:
        await cancel_support_request_handler(message, state, is_callback=False)
        return
    
    from users.models import SupportRequest
    user = await get_user_profile(message.from_user.id)
    if user:
        # Проверяем минимальную длину вопроса
        if len(message.text.strip()) < 5:
            await message.answer(
                "❌ Вопрос слишком короткий. Пожалуйста, опишите вашу проблему подробнее (минимум 5 символов).\n\n"
                "💡 Вы можете отменить запрос, нажав кнопку «Назад» или написав «Отмена».",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="cancel_support_request")]
                    ]
                )
            )
            return
        
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
        
        # Отправляем подтверждение пользователю
        confirmation_text = (
            "✅ <b>Ваш вопрос отправлен в техподдержку!</b>\n\n"
            "📧 Мы получили ваш запрос и обязательно ответим в ближайшее время.\n\n"
            "💬 Если у вас есть ещё вопросы, вы можете задать их через кнопку «Помощь» в главном меню."
        )
        await message.answer(confirmation_text, parse_mode='HTML')
    else:
        await send_not_registered_message(message, is_callback=False)
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
            await send_not_registered_message(callback_query, is_callback=True)
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
            await send_not_registered_message(callback_query, is_callback=True)
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
            await send_not_registered_message(callback_query, is_callback=True)
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

# Обработчик вебхука
async def handle_webhook(request):
    """
    Обработчик вебхука
    """
    try:
        data = await request.json()
        logger.info(f"Получены данные вебхука: {json.dumps(data, ensure_ascii=False)}")
        
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
        
        return web.Response(text='OK')
    except json.JSONDecodeError:
        logger.error("Invalid JSON")
        return web.Response(status=400, text='Invalid JSON')
    except Exception as e:
        logger.error(f"Ошибка в обработчике вебхука: {e}")
        return web.Response(status=500, text=str(e))

async def run_bot():
    """
    Запуск бота с поддержкой вебхуков
    """
    # Настраиваем приложение aiohttp
    app = web.Application()
    
    # Добавляем обработчик вебхука
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    
    # Устанавливаем команды бота
    await setup_bot_commands()
    
    # Устанавливаем вебхук
    webhook_info = await bot.get_webhook_info()
    current_url = webhook_info.url
    logger.info(f"Текущий URL вебхука: {current_url}")
    
    if current_url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=["message", "callback_query", "chat_member"]
        )
        logger.info(f"Вебхук успешно установлен на {WEBHOOK_URL}")

    # Запускаем сервер aiohttp
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8443)
    await site.start()

    logger.info("Бот запущен и слушает вебхуки на порту 8443")

    try:
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Ошибка в основном цикле бота: {e}")
    finally:
        await bot.delete_webhook()
        await runner.cleanup()

# Добавляем новые функции для работы с Яндекс Диском
async def init_yadisk():
    """
    Инициализация клиента Яндекс.Диска с использованием OAuth токена
    """
    try:
        y = yadisk.YaDisk(
            id=settings.YANDEX_DISK_CLIENT_ID,
            secret=settings.YANDEX_DISK_CLIENT_SECRET,
            token=settings.YANDEX_DISK_OAUTH_TOKEN
        )
        # Проверяем валидность токена
        if not await sync_to_async(y.check_token)():
            logger.error("Недействительный OAuth токен Яндекс.Диска")
            return None
        return y
    except Exception as e:
        logger.error(f"Ошибка при инициализации Яндекс.Диска: {e}")
        return None

async def save_file_to_yadisk(y: yadisk.YaDisk, file_path: str, save_path: str):
    """
    Сохраняет файл на Яндекс.Диск
    """
    try:
        with open(file_path, 'rb') as f:
            await sync_to_async(y.upload)(f, save_path)
            logger.info(f"Файл успешно загружен на Яндекс.Диск: {save_path}")
            return True
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла на Яндекс.Диск: {e}")
        return False

async def process_media_message(message: types.Message):
    """
    Обработка медиасообщений и сохранение их на Яндекс.Диск
    """
    from events_available.models import Events_offline, MediaFile
    from SGUevents.celery import check_deleted_message
    from datetime import datetime, timedelta
    
    logger.info(f"Начало обработки медиа-сообщения из чата {message.chat.id}")
    logger.info(f"Тип сообщения: {message.content_type}")
    
    # Определяем тип медиафайла и получаем информацию о нем
    file_info = None
    file_extension = None
    
    if message.photo:
        file_info = message.photo[-1]  # Берем последнее (самое качественное) фото
        file_extension = "jpg"
    elif message.video:
        file_info = message.video
        file_extension = "mp4"
    elif message.document:
        file_info = message.document
        file_extension = message.document.file_name.split('.')[-1] if '.' in message.document.file_name else 'unknown'
    
    if not file_info:
        logger.info("Медиафайл не найден в сообщении")
        return

    try:
        events = await sync_to_async(list)(
            Events_offline.objects.filter(
                users_chat_id=str(message.chat.id),
                save_media_to_disk=True
            ))
        logger.info(f"Найдено мероприятий для сохранения: {len(events)}")
    except Exception as e:
        logger.error(f"Ошибка при получении мероприятий: {e}")
        return

    if not events:
        logger.info("Нет мероприятий для сохранения медиафайлов")
        return

    event = events[0]
    y = yadisk.YaDisk(
        id=settings.YANDEX_DISK_CLIENT_ID,
        secret=settings.YANDEX_DISK_CLIENT_SECRET,
        token=settings.YANDEX_DISK_OAUTH_TOKEN
    )

    try:
        # Скачиваем файл
        file = await bot.get_file(file_info.file_id)
        local_path = f"temp_{file_info.file_id}.{file_extension}"
        await bot.download_file(file.file_path, local_path)
        
        # Создаем базовую директорию events, если её нет
        base_folder = "/events"
        if not await sync_to_async(y.exists)(base_folder):
            await sync_to_async(y.mkdir)(base_folder)
            logger.info(f"Создана базовая директория {base_folder}")

        # Создаем директорию мероприятия
        event_folder = f"{base_folder}/{event.name}"
        if not await sync_to_async(y.exists)(event_folder):
            await sync_to_async(y.mkdir)(event_folder)
            logger.info(f"Создана директория мероприятия {event_folder}")

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%H-%M-%S")
        yandex_filename = f"{timestamp}_{file_info.file_id}.{file_extension}"
        yandex_path = f"{event_folder}/{yandex_filename}"
            
        # Сохраняем файл на Яндекс.Диск
        if await save_file_to_yadisk(y, local_path, yandex_path):
            # Создаем запись в базе данных
            media_file = await sync_to_async(MediaFile.objects.create)(
                message_id=str(message.message_id),
                chat_id=str(message.chat.id),
                file_path=yandex_path
            )
            
            # Создаем отложенную задачу (1 час)
            task = check_deleted_message.apply_async(
                args=[media_file.id],
                countdown=3600  # 1 час
            )
            
            # Сохраняем ID задачи
            media_file.celery_task_id = task.id
            await sync_to_async(media_file.save)()
            
            logger.info(f"Создана задача Celery с ID {task.id} для проверки файла через 1 час")
        
        # Удаляем временный файл
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Временный файл {local_path} удален")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}")
        if 'local_path' in locals() and os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Временный файл {local_path} удален после ошибки")

# Обновляем обработчики медиафайлов
@router.message(F.photo)
@router.message(F.video)
@router.message(F.document)
async def handle_media(message: types.Message):
    logger.info(f"Получено сообщение типа: {message.content_type}")
    if message.photo:
        logger.info(f"Получено фото: {len(message.photo)} версий")
    await process_media_message(message)

@router.message(F.text == "\U00002754 Помощь")
async def help_request_button(message: types.Message, state: FSMContext):
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        # Формируем расширенное сообщение с пояснениями
        help_text = (
            "\U00002754 <b>Техподдержка</b>\n\n"
            "📝 <b>Вы можете задать вопрос по:</b>\n"
            "• Регистрации на мероприятия\n"
            "• Логистике и трансферам\n"
            "• Расписанию мероприятий\n"
            "• Техническим проблемам\n"
            "• Другим вопросам по платформе\n\n"
            "💡 <b>Примеры вопросов:</b>\n"
            "• Как отменить регистрацию на мероприятие?\n"
            "• Где найти информацию о логистике?\n"
            "• Как изменить данные профиля?\n\n"
            "✍️ <b>Напишите ваш вопрос ниже</b>, и мы обязательно вам поможем!\n\n"
            "💬 Вы также можете отменить запрос, нажав кнопку «Назад»."
        )
        
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="cancel_support_request"
                )]
            ]
        )
        
        await message.answer(help_text, reply_markup=keyboard, parse_mode='HTML')
        await state.set_state(SupportRequestForm.waiting_for_question)
    else:
        await send_not_registered_message(message, is_callback=False)

@router.message(F.text == "🌐 Портал")
async def portal_button(message: types.Message):
    # Проверяем, что это личный чат
    if message.chat.type != 'private':
        return
        
    user = await get_user_profile(message.from_user.id)
    if user:
        # Формируем URL портала (используем тот же домен, что для вебхука)
        base_url = WEBHOOK_HOST.rstrip('/') if WEBHOOK_HOST else "https://event.larin.work"
        miniapp_url = f"{base_url}/"
        
        # Создаем клавиатуру с кнопкой Mini App
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="🌐 Открыть портал",
                    web_app=types.WebAppInfo(url=miniapp_url)
                )]
            ]
        )
        
        await message.answer(
            f"🌐 Портал мероприятий СГУ\n\nНажмите кнопку ниже, чтобы открыть портал:",
            reply_markup=keyboard
        )
    else:
        await send_not_registered_message(message, is_callback=False)

@router.callback_query(F.data.startswith("logistics_"))
async def show_logistics_info(callback_query: types.CallbackQuery):
    """Показывает информацию о логистике для мероприятия"""
    try:
        from events_available.models import EventLogistics
        from django.utils.timezone import localtime
        
        # Извлекаем ID мероприятия из callback_data
        event_id = callback_query.data.split("_")[1]
        
        # Получаем пользователя
        user = await get_user_profile(callback_query.from_user.id)
        if not user:
            await send_not_registered_message(callback_query, is_callback=True)
            return
        
        # Получаем информацию о логистике
        logistics = await sync_to_async(EventLogistics.objects.select_related('event').get)(
            user=user, 
            event_id=event_id
        )
        
        # Получаем название и ссылку мероприятия
        event_link = None
        if logistics.event:
            from users.telegram_utils import get_event_url, create_event_hyperlink
            event_url = await sync_to_async(get_event_url)(logistics.event)
            event_link = await sync_to_async(create_event_hyperlink)(logistics.event.name, event_url)
        
        # Формируем красивый текст с информацией о логистике
        logistics_text = ""
        if event_link:
            logistics_text = f"🎯 <b>{event_link}</b>\n\n"
        logistics_text += "✈️ <b>Информация о логистике</b>\n\n"
        
        # Информация о прилете
        if logistics.arrival_datetime:
            arrival_local = localtime(logistics.arrival_datetime)
            logistics_text += f"🛬 <b>Прилет:</b>\n"
            logistics_text += f"📅 {arrival_local.strftime('%d.%m.%Y %H:%M')}\n"
            
            if logistics.arrival_flight_number:
                logistics_text += f"✈️ Рейс: {logistics.arrival_flight_number}\n"
            if logistics.arrival_airport:
                logistics_text += f"🏢 Аэропорт: {logistics.arrival_airport}\n"
            logistics_text += "\n"
        
        # Информация об улете
        if logistics.departure_datetime:
            departure_local = localtime(logistics.departure_datetime)
            logistics_text += f"🛫 <b>Улет:</b>\n"
            logistics_text += f"📅 {departure_local.strftime('%d.%m.%Y %H:%M')}\n"
            
            if logistics.departure_flight_number:
                logistics_text += f"✈️ Рейс: {logistics.departure_flight_number}\n"
            if logistics.departure_airport:
                logistics_text += f"🏢 Аэропорт: {logistics.departure_airport}\n"
            logistics_text += "\n"
        
        # Информация о трансфере
        if logistics.transfer_needed:
            logistics_text += f"🚗 <b>Трансфер:</b> Требуется\n\n"
        else:
            logistics_text += f"🚗 <b>Трансфер:</b> Не требуется\n\n"

        # Информация о встречающем
        if logistics.meeting_person:
            logistics_text += f"🚗 <b>Встречающий:</b>\n{logistics.meeting_person}\n\n"
        
        # Информация о гостинице
        if logistics.hotel_details:
            logistics_text += f"🏨 <b>Гостиница:</b>\n{logistics.hotel_details}\n\n"
        
        # Если нет никакой информации
        if not any([logistics.arrival_datetime, logistics.departure_datetime, logistics.hotel_details]):
            logistics_text += "ℹ️ Подробная информация о логистике пока не заполнена."
        
        # Добавляем указание часового пояса
        if logistics.arrival_datetime or logistics.departure_datetime:
            logistics_text += "\n\n⌚ Время указано по местному времени."
        
        # Отправляем информацию
        await callback_query.message.answer(
            logistics_text,
            parse_mode='HTML'
        )
        await callback_query.answer()
        
    except EventLogistics.DoesNotExist:
        await callback_query.answer("Логистическая информация не найдена.")
    except Exception as e:
        logger.error(f"Ошибка при показе логистики: {e}")
        await callback_query.answer("Произошла ошибка при загрузке информации.")

@router.callback_query(F.data == "mytasks")
async def list_task_events(callback_query: types.CallbackQuery):
    user = await get_user_profile(callback_query.from_user.id)
    if not user:
        await send_not_registered_message(callback_query, is_callback=True)
        return

    from events_available.models import EventOfflineCheckList, Events_offline
    tasks = await sync_to_async(list)(
        EventOfflineCheckList.objects.filter(responsible=user, completed=False).select_related('event')
    )
    if not tasks:
        await callback_query.answer("Активных задач нет", show_alert=True)
        return

    # Группируем по мероприятиям
    event_id_to_tasks = {}
    for t in tasks:
        event_id_to_tasks.setdefault(t.event_id, []).append(t)

    # Отправляем по мероприятию название и кнопку показать задачи
    from users.telegram_utils import get_event_url, create_event_hyperlink
    for event_id, tlist in event_id_to_tasks.items():
        try:
            event_obj = await sync_to_async(Events_offline.objects.get)(id=event_id)
        except Events_offline.DoesNotExist:
            continue
        event_url = await sync_to_async(get_event_url)(event_obj)
        event_link = await sync_to_async(create_event_hyperlink)(event_obj.name, event_url)
        text = f"📌 {event_link}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"Показать задачи ({len(tlist)})", callback_data=f"mytasks_event_{event_id}")]])
        await callback_query.message.answer(text, reply_markup=kb, parse_mode='HTML')

    await callback_query.answer()

@router.callback_query(F.data.startswith("mytasks_event_"))
async def show_event_tasks(callback_query: types.CallbackQuery):
    user = await get_user_profile(callback_query.from_user.id)
    if not user:
        await send_not_registered_message(callback_query, is_callback=True)
        return
    try:
        _, _, event_id_str = callback_query.data.partition("mytasks_event_")
        event_id = int(event_id_str)
    except Exception:
        await callback_query.answer("Некорректный запрос", show_alert=True)
        return

    from events_available.models import EventOfflineCheckList, Events_offline
    tasks = await sync_to_async(list)(
        EventOfflineCheckList.objects.filter(responsible=user, completed=False, event_id=event_id).select_related('task_name', 'event')
    )
    if not tasks:
        await callback_query.answer("Задачи не найдены", show_alert=True)
        return

    # Сортировка по сроку (сначала ближайшие, без срока в конце)
    tasks_sorted = sorted(tasks, key=lambda t: (t.planned_date is None, t.planned_date or date.max))

    for t in tasks_sorted:
        task_name = str(t.task_name) if t.task_name else 'Задача'
        deadline = t.planned_date.strftime('%d.%m.%Y') if t.planned_date else 'не указан'
        text = f"• {task_name}\nСрок: {deadline}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Отметить завершенной", callback_data=f"mark_done_{t.id}")]])
        await callback_query.message.answer(text, reply_markup=kb)

    await callback_query.answer()

@router.callback_query(F.data.startswith("mark_done_"))
async def mark_task_done(callback_query: types.CallbackQuery):
    user = await get_user_profile(callback_query.from_user.id)
    if not user:
        await send_not_registered_message(callback_query, is_callback=True)
        return

    try:
        _, _, task_id_str = callback_query.data.partition("mark_done_")
        task_id = int(task_id_str)
    except Exception:
        await callback_query.answer("Некорректный запрос", show_alert=True)
        return

    from events_available.models import EventOfflineCheckList
    try:
        task = await sync_to_async(EventOfflineCheckList.objects.select_related('responsible').get)(id=task_id)
    except EventOfflineCheckList.DoesNotExist:
        await callback_query.answer("Задача не найдена", show_alert=True)
        return

    if not task.responsible or str(task.responsible_id) != str(user.id):
        await callback_query.answer("Недостаточно прав для изменения задачи", show_alert=True)
        return

    # Обновляем задачу: выполнена + дата выполнения
    def _complete_task():
        task.completed = True
        task.actual_date = timezone.localdate()
        task.save(update_fields=["completed", "actual_date"])
    await sync_to_async(_complete_task)()

    # Пытаемся удалить сообщение с задачей
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    except Exception:
        try:
            await callback_query.message.edit_text("✅ Задача отмечена как выполненная")
        except Exception:
            pass

    await callback_query.answer("Готово")

if __name__ == "__main__":
    setup_django_environment()
    asyncio.run(run_bot())
