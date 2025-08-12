import json
import logging
import os
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from transliterate import translit
from asgiref.sync import async_to_sync
from bot.main import handle_webhook
from django.utils.timezone import now
from datetime import datetime


from .forms import RegistrationForm, UserPasswordChangeForm
from .models import Department, AdminRightRequest, TelegramAuthToken
from .telegram_utils import send_registration_details_sync, send_password_change_details_sync
from .telegram_utils import send_confirmation_to_user, send_message_to_support_chat
from events_available.models import EventLogistics

User = get_user_model()
logger = logging.getLogger(__name__)

DEV_BOT_NAME = os.getenv('DEV_BOT_NAME')
BOT_NAME = os.getenv('BOT_NAME')

def transliterate_to_eng(text):
    """
    Транслитерация текста с русского на английский
    """
    return translit(text, 'ru', reversed=True).lower().replace(' ', '')

def generate_random_password():
    """
    Генерация случайного пароля
    """
    return get_random_string(12)

def home(request):
    return render(request, 'users/home.html')

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            generated_password = get_random_string(8)
            department_id = form.cleaned_data['department_id']
            department, _ = Department.objects.get_or_create(department_id=department_id)

            user_kwargs = {
                'email': form.cleaned_data.get('email'),
                'password': generated_password,
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'middle_name': form.cleaned_data.get('middle_name', ''),
                'department': department,
                'telegram_id': form.cleaned_data['telegram_id'],
            }
            new_user = User.objects.create_user(**user_kwargs)

            # Отправляем данные регистрации в Telegram, если указан telegram_id
            if new_user.telegram_id:
                send_registration_details_sync(new_user.telegram_id, new_user.username, generated_password)

            return redirect('users:login')
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME,
    }
    return render(request, 'users/register.html', context)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            request.session['login_method'] = 'Через логин и пароль'
            # Перенаправляем на next URL если он есть, иначе на главную
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main:index')
        else:
            messages.error(request, "Неверный логин или пароль.")
    context = {
        'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME,
        'next': request.GET.get('next', '')
    }
    return render(request, 'users/login.html', context)

@csrf_exempt
def telegram_auth(request, token):
    """
    Обработка авторизации через Telegram
    """
    try:
        with transaction.atomic():
            auth_token = TelegramAuthToken.objects.select_for_update().get(token=token)
            
            # Если токен уже использован, просто показываем страницу входа
            if auth_token.is_used:
                return render(request, 'users/telegram_login.html', {
                    'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME
                })
            
            if not auth_token.is_valid():
                logger.warning(f"Токен недействителен: is_used={auth_token.is_used}, expires_at={auth_token.expires_at}")
                return render(request, 'users/telegram_login.html', {
                    'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME
                })

            # Создаем отдел если не существует
            department, _ = Department.objects.get_or_create(
                department_id=auth_token.department_id,
                defaults={'department_name': f'Отдел {auth_token.department_id}'}
            )
            
            # Генерируем пароль до создания пользователя
            password = get_random_string(8)
            
            # Создаем пользователя используя CustomUserManager
            user_kwargs = {
                'first_name': auth_token.first_name,
                'last_name': auth_token.last_name,
                'middle_name': auth_token.middle_name,
                'department': department,
                'telegram_id': auth_token.telegram_id,
                'password': password
            }
            
            user = User.objects.create_user(**user_kwargs)
            logger.info(f"Создан новый пользователь: {user.username}")
            
            # Автоматическая загрузка аватара из Telegram отключена
            
            # Отправляем данные для входа в Telegram
            try:
                send_registration_details_sync(auth_token.telegram_id, user.username, password)
                logger.info(f"Данные для входа отправлены пользователю {user.username}")
            except Exception as e:
                logger.error(f"Ошибка при отправке данных для входа: {str(e)}")
            
            # Помечаем токен как использованный
            auth_token.is_used = True
            auth_token.save()
            logger.info(f"Токен помечен как использованный")
            
            # После успешной регистрации показываем страницу входа
            return render(request, 'users/telegram_login.html', {
                'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME
            })
            
    except TelegramAuthToken.DoesNotExist:
        logger.error(f"Токен не найден в базе: {token}")
        return render(request, 'users/telegram_login.html', {
            'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME
        })
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {str(e)}")
        return render(request, 'users/telegram_login.html', {
            'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME
        })

@csrf_exempt
@login_required
def change_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'}, status=405)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = request.POST

    form = UserPasswordChangeForm(data)
    if not form.is_valid():
        errors = form.errors.get('__all__') or sum(form.errors.values(), [])
        return JsonResponse({'success': False, 'error': '\n'.join(errors)})

    new_password = form.cleaned_data['new_password1']
    request.user.set_password(new_password)
    request.user.save()

    # Отправляем уведомление в Telegram (без самого пароля), если привязан Telegram
    if getattr(request.user, 'telegram_id', None):
        try:
            send_password_change_details_sync(request.user.telegram_id, request.user.username, None)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления в Telegram: {str(e)}")

    logout(request)
    return JsonResponse({'success': True, 'message': 'Пароль изменён. Выполните вход с новым паролем.'})

@csrf_exempt
@login_required
def request_admin_rights(request):
    if request.method == 'POST':
        try:
            # Проверяем, есть ли уже активный запрос от этого пользователя
            existing_request = AdminRightRequest.objects.filter(user=request.user, status='pending').first()
            if existing_request:
                logger.info(f"Найден существующий запрос от пользователя {request.user.username}")
                return JsonResponse({'success': False, 'message': 'Ваш запрос на админские права уже рассматривается.'})

            data = json.loads(request.body)
            justification = data.get('reason', '')
            user_full_name = f"{request.user.last_name} {request.user.first_name} {' ' + request.user.middle_name if request.user.middle_name else ''}".strip()
            message = f"Запрос на админские права от {user_full_name}: {justification}"
            
            logger.info(f"Подготовлено сообщение для отправки: {message}")

            # Создание новой записи запроса на админские права
            new_request = AdminRightRequest(user=request.user, reason=justification)
            new_request.save()
            logger.info(f"Создан новый запрос на админские права в базе данных")

            # Отправка сообщения в чат поддержки
            try:
                logger.info(f"Попытка отправки сообщения в чат поддержки. Chat ID: {settings.ACTIVE_TELEGRAM_SUPPORT_CHAT_ID}")
                send_message_to_support_chat(message)
                logger.info("Сообщение успешно отправлено в чат поддержки")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в чат поддержки: {str(e)}")

            # Уведомление пользователя о том, что запрос отправлен
            try:
                logger.info(f"Попытка отправки подтверждения пользователю. Telegram ID: {request.user.telegram_id}")
                send_confirmation_to_user(request.user.telegram_id)
                logger.info("Подтверждение успешно отправлено пользователю")
            except Exception as e:
                logger.error(f"Ошибка при отправке подтверждения пользователю: {str(e)}")

            return JsonResponse({'success': True, 'message': 'Запрос на админские права отправлен в чат поддержки и зарегистрирован в системе.'})
        except json.JSONDecodeError:
            logger.error("Ошибка при декодировании JSON из запроса")
            return JsonResponse({'success': False, 'error': 'Ошибка в формате данных.'})
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке запроса: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при обработке запроса.'})
    return JsonResponse({'success': False, 'error': 'Недопустимый запрос.'})

@login_required
def profile(request):
    user = request.user
    login_method = request.session.get('login_method', 'Неизвестный способ входа')
    department_name = user.department.department_name if user.department else 'Не указан'
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    today = timezone.make_aware(today)
    logistics = EventLogistics.objects.filter(user=user, departure_datetime__gte=today).order_by('departure_datetime')
    return render(request, 'users/profile.html', {'user': user, 'login_method': login_method, 'department_name': department_name, 'logistics': logistics,})
    # login_method = request.session.get('login_method', 'Неизвестный способ входа')
    # department_name = request.user.department.department_name if request.user.department else 'Не указан'
    # logistics = EventLogistics.objects.filter(user=request.user)
    # print(logistics)
    # return render(request, 'users/profile.html', {'user': request.user, 'login_method': login_method, 'department_name': department_name, 'logistics': logistics,})

@login_required
def logout(request):
    auth.logout(request)
    return redirect(reverse('main:index'))

def general(request):
    return render(request, 'main/index.html')

@csrf_exempt
def telegram_webhook(request):
    """
    Обработчик вебхука для Django
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Получены данные вебхука: {json.dumps(data, ensure_ascii=False)}")
        
        # Импортируем здесь, чтобы избежать циклической зависимости
        from bot.main import bot, dp
        from telegram import Update
        
        update = Update(**data)
        async_to_sync(dp.feed_update)(bot=bot, update=update)
        
        return JsonResponse({'status': 'ok'})
    except json.JSONDecodeError:
        logger.error("Invalid JSON")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка в обработчике вебхука: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def telegram_login_callback(request):
    """
    Обработка входа через Telegram после нажатия на виджет
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(f"Получены данные от виджета Telegram: {data}")
            
            # Telegram виджет может отправить id в разных форматах
            telegram_id = str(data.get('id') or data.get('telegram_id'))
            next_url = data.get('next')
            
            if not telegram_id:
                logger.error("Telegram ID отсутствует в данных")
                return JsonResponse({'success': False, 'error': 'Не указан Telegram ID'})
            
            logger.info(f"Поиск пользователя с telegram_id: {telegram_id}")
            user = User.objects.filter(telegram_id=telegram_id).first()
            
            if not user:
                logger.error(f"Пользователь с telegram_id {telegram_id} не найден")
                return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
            
            logger.info(f"Пользователь найден: {user.username}")
            
            # Автоматическая загрузка аватара из Telegram отключена
            
            # Используем authenticate для проверки пользователя
            authenticated_user = authenticate(request, telegram_id=telegram_id)
            if authenticated_user is None:
                logger.error(f"Ошибка аутентификации пользователя с telegram_id {telegram_id}")
                return JsonResponse({'success': False, 'error': 'Ошибка аутентификации'})
            
            auth_login(request, authenticated_user)
            request.session['login_method'] = 'Через Telegram'
            
            # Перенаправляем на next URL если он есть, иначе на главную
            redirect_url = next_url if next_url else reverse('main:index')
            return JsonResponse({'success': True, 'redirect_url': redirect_url})
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Неверный формат данных'})
        except Exception as e:
            logger.error(f"Ошибка при входе через Telegram: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при входе'})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

@csrf_exempt
@login_required
def event_support_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_id = data.get('event_id')
            model_type = data.get('model_type')
            question = data.get('question')

            if not all([event_id, model_type, question]):
                return JsonResponse({'success': False, 'error': 'Не все необходимые данные предоставлены'})

            # Получаем модель в зависимости от типа мероприятия
            if model_type == 'offline':
                from events_available.models import Events_offline as EventModel
            elif model_type == 'online':
                from events_available.models import Events_online as EventModel
            else:
                return JsonResponse({'success': False, 'error': 'Неверный тип мероприятия'})

            # Получаем мероприятие
            event = EventModel.objects.get(id=event_id)
            if not event.support_chat_id:
                return JsonResponse({'success': False, 'error': 'Для данного мероприятия не настроен чат поддержки'})

            # Формируем сообщение с HTML разметкой
            user_link = f'<a href="tg://user?id={request.user.telegram_id}">{request.user.first_name} {request.user.last_name}</a>'
            message = (
                f"Вопрос по мероприятию \"{event.name}\" от {user_link}:\n\n"
                f"<pre>{question}</pre>"
            )

            # Отправляем сообщение в чат поддержки мероприятия
            from users.telegram_utils import send_message_to_event_support_chat
            if send_message_to_event_support_chat(message, event.support_chat_id):
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Ошибка отправки сообщения'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат данных'})
        except EventModel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Мероприятие не найдено'})
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса в поддержку: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при обработке запроса'})

    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

@csrf_exempt
@login_required
def upload_photo(request):
    """
    Загрузка фото профиля пользователя
    """
    if request.method == 'POST':
        try:
            if 'photo' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'Фото не выбрано'})
            
            photo = request.FILES['photo']
            
            # Проверяем тип файла
            if not photo.content_type.startswith('image/'):
                return JsonResponse({'success': False, 'error': 'Файл должен быть изображением'})
            
            # Проверяем размер файла (не более 10MB)
            if photo.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': 'Размер файла не должен превышать 10MB'})
            
            # Удаляем старое фото если есть
            if request.user.profile_photo:
                old_photo_path = request.user.profile_photo.path
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
            
            # Сохраняем новое фото
            request.user.profile_photo = photo
            request.user.save()
            
            logger.info(f"Пользователь {request.user.username} загрузил новое фото профиля")
            return JsonResponse({'success': True, 'message': 'Фото успешно загружено'})
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке фото: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при загрузке фото'})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

@csrf_exempt
@login_required
def delete_photo(request):
    """
    Удаление фото профиля пользователя
    """
    if request.method == 'POST':
        try:
            if not request.user.profile_photo:
                return JsonResponse({'success': False, 'error': 'У вас нет загруженного фото'})
            
            # Удаляем файл с диска
            photo_path = request.user.profile_photo.path
            if os.path.exists(photo_path):
                os.remove(photo_path)
            
            # Очищаем поле в базе данных
            request.user.profile_photo = None
            request.user.save()
            
            logger.info(f"Пользователь {request.user.username} удалил фото профиля")
            return JsonResponse({'success': True, 'message': 'Фото успешно удалено'})
            
        except Exception as e:
            logger.error(f"Ошибка при удалении фото: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при удалении фото'})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

@csrf_exempt
@login_required
def fetch_telegram_photo(request):
    """
    Ручная загрузка фото профиля пользователя из Telegram
    """
    if request.method == 'POST':
        try:
            if not request.user.telegram_id:
                return JsonResponse({'success': False, 'error': 'Telegram ID не указан. Войдите через Telegram, чтобы связать аккаунт.'})

            from .telegram_utils import download_telegram_avatar
            avatar_file = download_telegram_avatar(request.user.telegram_id)

            if not avatar_file:
                return JsonResponse({'success': False, 'error': 'Не удалось получить фото из Telegram. Убедитесь, что в Telegram установлено фото профиля.'})

            # Удаляем старое фото если есть
            if request.user.profile_photo:
                try:
                    old_photo_path = request.user.profile_photo.path
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)
                except Exception:
                    # Не критично, просто залогируем
                    logger.warning('Не удалось удалить старое фото профиля перед обновлением из Telegram')

            # Сохраняем новое фото
            request.user.profile_photo.save(avatar_file.name, avatar_file, save=True)
            logger.info(f"Пользователь {request.user.username} обновил фото профиля из Telegram")
            return JsonResponse({'success': True, 'message': 'Фото профиля из Telegram успешно загружено'})

        except Exception as e:
            logger.error(f"Ошибка при ручной загрузке фото из Telegram: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Произошла ошибка при загрузке фото из Telegram'})

    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})
