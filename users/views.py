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
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime


from .forms import RegistrationForm, UserPasswordChangeForm
from .models import Department, AdminRightRequest, TelegramAuthToken, PasswordResetCode
from .telegram_utils import send_registration_details_sync, send_password_change_details_sync
from .telegram_utils import send_confirmation_to_user, send_message_to_support_chat
from .telegram_utils import send_password_reset_warning, send_password_reset_code
from events_available.models import EventLogistics, Events_offline
from bookmarks.models import Registered
from users.forms import EventLogisticsForm


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
    Обработка авторизации через Telegram: автоматический логин и редирект
    """
    try:
        with transaction.atomic():
            auth_token = TelegramAuthToken.objects.select_for_update().get(token=token)
            
            # Если токен уже использован - редирект на главную (пользователь уже зарегистрирован)
            if auth_token.is_used:
                logger.warning(f"Токен уже использован: {token}")
                return redirect('main:index')
            
            if not auth_token.is_valid():
                logger.warning(f"Токен недействителен: is_used={auth_token.is_used}, expires_at={auth_token.expires_at}")
                messages.error(request, "Ссылка недействительна или истекла срок действия.")
                return redirect('users:login')

            # Проверяем, существует ли уже пользователь с таким telegram_id
            user = User.objects.filter(telegram_id=auth_token.telegram_id).first()
            
            # Получаем пароль из токена (сгенерирован в боте)
            password = auth_token.password
            
            if not user:
                # Создаем отдел если не существует
                department, _ = Department.objects.get_or_create(
                    department_id=auth_token.department_id,
                    defaults={'department_name': f'Отдел {auth_token.department_id}'}
                )
                
                # Создаем пользователя используя пароль из токена
                user_kwargs = {
                    'first_name': auth_token.first_name,
                    'last_name': auth_token.last_name,
                    'middle_name': auth_token.middle_name,
                    'department': department,
                    'telegram_id': auth_token.telegram_id,
                    'password': password  # Используем пароль из токена
                }
                
                user = User.objects.create_user(**user_kwargs)
                logger.info(f"Создан новый пользователь: {user.username}")
            else:
                # Если пользователь уже существует, обновляем пароль на пароль из токена (чтобы логин сработал)
                user.set_password(password)
                user.save()
                logger.info(f"Пароль обновлен для существующего пользователя {user.username}")
            
            # Помечаем токен как использованный (одноразовая ссылка) ПЕРЕД логином
            auth_token.is_used = True
            auth_token.save()
            logger.info(f"Токен помечен как использованный")
            
            # Логиним пользователя напрямую (без промежуточных страниц)
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['login_method'] = 'Через Telegram (по логину/паролю)'
            logger.info(f"Пользователь {user.username} успешно авторизован")
            
            # Отправляем итоговые учетные данные пользователю в Telegram
            send_registration_details_sync(auth_token.telegram_id, user.username, password)
            logger.info(f"Итоговые данные для входа отправлены пользователю {user.username}")

            # Редирект на главную (без промежуточной страницы)
            return redirect('main:index')
            
    except TelegramAuthToken.DoesNotExist:
        logger.error(f"Токен не найден в базе: {token}")
        messages.error(request, "Неверная ссылка регистрации.")
        return redirect('users:login')
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {str(e)}")
        messages.error(request, "Произошла ошибка при регистрации. Попробуйте позже.")
        return redirect('users:login')

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
    department_name = user.department.department_name if getattr(user, "department", None) else 'Не указан'

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logistics = (
        EventLogistics.objects
        .filter(user=user)
        .filter(
            Q(departure_datetime__gte=today) |
            Q(departure_datetime__isnull=True, arrival_datetime__gte=today) |
            Q(arrival_datetime__lte=today, departure_datetime__gte=today)
        )
        .order_by(Coalesce('departure_datetime', 'arrival_datetime'))
        .select_related('event')
    )

    registered = (Registered.objects
                  .filter(user=user, offline__isnull=False)
                  .select_related('offline'))

    open_logistics_modal = False  # <— флаг

    # Локальные хелперы форматирования и отправки
    def _fmt(field_name, value):
        if field_name in ("arrival_datetime", "departure_datetime") and value:
            return value.astimezone(timezone.get_current_timezone()).strftime("%d.%m.%Y %H:%M")
        if field_name == "transfer_needed":
            return "Нужен" if value else "Не нужен"
        return value if (value not in (None, "")) else "—"
    
    def _notify_support_changes(event, changes, created=False):
        try:
            support_chat_id = getattr(event, 'support_chat_id', None)
            if not support_chat_id:
                return
            from users.telegram_utils import send_text_to_chat
            user_full = f"{user.last_name} {user.first_name}".strip()
            intro = "добавил свою логистику" if created else "внёс изменения в свою логистику"
            lines = [f"✈️ Пользователь {user_full} {intro} по мероприятию \"{event.name}\":"]
            for field, old_v, new_v in changes:
                lines.append(f"- {field}: {old_v} → {new_v}")
            text = "\n".join(lines)
            send_text_to_chat(support_chat_id, text, parse_html=False)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об изменениях логистики: {e}")
    
    if request.method == "POST" and request.POST.get("form_name") == "logistics":
        form = EventLogisticsForm(request.POST, user=user)
        if form.is_valid():
            event = form.cleaned_data["event"]
            if not form.fields["event"].queryset.filter(pk=event.pk).exists():
                messages.error(request, "Вы не зарегистрированы на выбранное мероприятие.")
                return redirect("users:profile")

            # Снимем старые значения для diff
            fields_list = [
                "arrival_datetime","arrival_flight_number","arrival_airport",
                "departure_datetime","departure_flight_number","departure_airport",
                "transfer_needed","hotel_details","meeting_person"
            ]
            old = None
            created_instance = False
            instance = EventLogistics.objects.filter(user=user, event=event).first()
            if instance:
                old = {f: getattr(instance, f) for f in fields_list}
            else:
                instance = EventLogistics(user=user, event=event)
                created_instance = True
            
            for f in fields_list:
                setattr(instance, f, form.cleaned_data.get(f))
            instance.save()
            messages.success(request, "Логистика сохранена.")
            
            # Подготовим diff и уведомим чат поддержки
            changes = []
            if created_instance:
                for f in fields_list:
                    new_v = _fmt(f, getattr(instance, f))
                    changes.append((instance._meta.get_field(f).verbose_name, "—", new_v))
                _notify_support_changes(event, changes, created=True)
            else:
                for f in fields_list:
                    old_v = old.get(f)
                    new_v_raw = getattr(instance, f)
                    if old_v != new_v_raw:
                        changes.append((instance._meta.get_field(f).verbose_name, _fmt(f, old_v), _fmt(f, new_v_raw)))
                if changes:
                    _notify_support_changes(event, changes, created=False)
            
            return redirect('users:profile')
        else:
            # Если ошибки — откроем модалку заново
            open_logistics_modal = True
    else:
        form = EventLogisticsForm(user=user)

    return render(
        request,
        "users/profile.html",
        {
            "user": user,
            "login_method": login_method,
            "department_name": department_name,
            "logistics": logistics,
            "registered": registered,
            "logistics_form": form,
            "open_logistics_modal": open_logistics_modal,  # <—
        }
    )


# --- AJAX: инлайн‑обновление одного поля без перезагрузки ---
ALLOWED_FIELDS = {
    "arrival_datetime", "arrival_flight_number", "arrival_airport",
    "departure_datetime", "departure_flight_number", "departure_airport",
    "transfer_needed", "hotel_details", "meeting_person",
}

@login_required
def update_logistics_field(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    field = data.get("field")
    raw_value = data.get("value")

    if field not in ALLOWED_FIELDS:
        return HttpResponseBadRequest("Field not allowed")

    logist = EventLogistics.objects.filter(pk=pk, user=request.user).first()
    if not logist:
        return HttpResponseForbidden("No access")

    # Снимем старое значение
    old_value = getattr(logist, field)

    # Преобразование типов
    value = raw_value
    if field in ("arrival_datetime", "departure_datetime"):
        if raw_value and len(raw_value) == 16:
            raw_value = raw_value + ":00"
        dt = parse_datetime(raw_value) if raw_value else None
        if dt is not None and timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_default_timezone())
        value = dt
    elif field == "transfer_needed":
        value = True if str(raw_value).lower() in ("1", "true", "on", "yes") else False

    setattr(logist, field, value)
    try:
        logist.full_clean()
        logist.save()
    except Exception as e:
        return HttpResponseBadRequest(str(e))

    # Ответ для отображения
    def _fmt_field(fname, val):
        if fname in ("arrival_datetime", "departure_datetime") and val:
            return val.astimezone(timezone.get_current_timezone()).strftime("%d.%m.%Y %H:%M")
        if fname == "transfer_needed":
            return "Нужен" if val else "Не нужен"
        return val if (val not in (None, "")) else "—"
    
    pretty = _fmt_field(field, value)
    
    # Уведомление в чат поддержки только если значение реально изменилось
    if old_value != value:
        try:
            event = logist.event
            support_chat_id = getattr(event, 'support_chat_id', None)
            if support_chat_id:
                from users.telegram_utils import send_text_to_chat
                user_full = f"{request.user.last_name} {request.user.first_name}".strip()
                old_fmt = _fmt_field(field, old_value)
                new_fmt = _fmt_field(field, value)
                field_verbose = logist._meta.get_field(field).verbose_name
                text = (
                    f"✈️ Пользователь {user_full} внёс изменения в свою логистику по мероприятию \"{event.name}\":\n"
                    f"- {field_verbose}: {old_fmt} → {new_fmt}"
                )
                send_text_to_chat(support_chat_id, text, parse_html=False)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об изменении логистики (AJAX): {e}")
    
    return JsonResponse({"ok": True, "field": field, "value": pretty})

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

@login_required
def get_logistics_for_event(request):
    """
    Возвращает сохранённую логистику текущего пользователя по выбранному оффлайн‑мероприятию.
    GET-параметры: event_id
    Ответ JSON: {exists: bool, fields...}
    Дата/время в формате для input[type=datetime-local]: YYYY-MM-DDTHH:MM
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)

    event_id = request.GET.get('event_id')
    if not event_id:
        return JsonResponse({'success': False, 'error': 'Не указан event_id'}, status=400)

    try:
        event = Events_offline.objects.get(pk=event_id)
    except Events_offline.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Мероприятие не найдено'}, status=404)

    logist = EventLogistics.objects.filter(user=request.user, event=event).first()
    if not logist:
        return JsonResponse({'exists': False})

    tz = timezone.get_current_timezone()

    def fmt_dt(dt):
        if not dt:
            return ''
        aware = dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.get_default_timezone())
        local_dt = aware.astimezone(tz)
        return local_dt.strftime('%Y-%m-%dT%H:%M')

    data = {
        'exists': True,
        'arrival_datetime': fmt_dt(logist.arrival_datetime),
        'arrival_flight_number': logist.arrival_flight_number or '',
        'arrival_airport': logist.arrival_airport or '',
        'departure_datetime': fmt_dt(logist.departure_datetime),
        'departure_flight_number': logist.departure_flight_number or '',
        'departure_airport': logist.departure_airport or '',
        'transfer_needed': bool(logist.transfer_needed),
        'hotel_details': logist.hotel_details or '',
        'meeting_person': logist.meeting_person or '',
    }

    return JsonResponse(data)

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

def password_reset_request(request):
    """
    Обработка запроса на восстановление пароля
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            messages.error(request, 'Пожалуйста, введите логин')
            return render(request, 'users/password_reset.html', {'step': 'username'})
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Не показываем, что пользователь не найден (безопасность)
            messages.success(request, 'Если пользователь с таким логином существует и к нему привязан Telegram, код восстановления будет отправлен.')
            return render(request, 'users/password_reset.html', {'step': 'username'})
        
        # Проверяем наличие telegram_id
        if not user.telegram_id:
            messages.error(request, 'К данному аккаунту не привязан Telegram. Восстановление пароля невозможно.')
            return render(request, 'users/password_reset.html', {'step': 'username'})
        
        # Проверяем существующие активные коды
        existing_code = PasswordResetCode.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_code:
            # Если код уже существует и можно отправить повторно
            if existing_code.can_resend():
                # Генерируем новый код
                new_code = ''.join([str(get_random_string(1, allowed_chars='0123456789')) for _ in range(6)])
                existing_code.code = new_code
                existing_code.last_resend_at = timezone.now()
                existing_code.resend_count += 1
                existing_code.save()
                
                # Отправляем предупреждение и код
                send_password_reset_warning(user.telegram_id, user.username)
                send_password_reset_code(user.telegram_id, new_code)
                
                messages.success(request, 'Код восстановления отправлен повторно в Telegram.')
            else:
                # Нельзя отправить повторно - показываем форму ввода кода
                if existing_code.resend_count >= 3:
                    messages.error(request, 'Превышено максимальное количество попыток отправки. Попробуйте позже.')
                    return render(request, 'users/password_reset.html', {'step': 'username'})
                
                # Вычисляем время до следующей отправки
                time_since_last = timezone.now() - existing_code.last_resend_at if existing_code.last_resend_at else timezone.timedelta(seconds=0)
                seconds_remaining = max(0, 30 - int(time_since_last.total_seconds()))
                
                messages.info(request, f'Код уже отправлен. Повторная отправка возможна через {seconds_remaining} секунд.')
            
            return render(request, 'users/password_reset.html', {
                'step': 'code',
                'username': username,
                'reset_code_id': existing_code.id
            })
        
        # Создаем новый код
        reset_code = ''.join([str(get_random_string(1, allowed_chars='0123456789')) for _ in range(6)])
        password_reset_code = PasswordResetCode.objects.create(
            user=user,
            code=reset_code,
            last_resend_at=timezone.now(),
            resend_count=1
        )
        
        # Отправляем предупреждение и код
        send_password_reset_warning(user.telegram_id, user.username)
        send_password_reset_code(user.telegram_id, reset_code)
        
        messages.success(request, 'Код восстановления отправлен в Telegram.')
        return render(request, 'users/password_reset.html', {
            'step': 'code',
            'username': username,
            'reset_code_id': password_reset_code.id
        })
    
    return render(request, 'users/password_reset.html', {'step': 'username'})

@csrf_exempt
def password_reset_verify(request):
    """
    Проверка кода восстановления и смена пароля
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    try:
        data = json.loads(request.body) if request.body else {}
        code = data.get('code', '').strip()
        reset_code_id = data.get('reset_code_id')
        username = data.get('username', '').strip()
        
        if not code or not reset_code_id or not username:
            return JsonResponse({'success': False, 'error': 'Не все данные предоставлены'})
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        
        try:
            reset_code_obj = PasswordResetCode.objects.get(id=reset_code_id, user=user)
        except PasswordResetCode.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Код восстановления не найден'})
        
        # Проверяем валидность кода
        if not reset_code_obj.is_valid():
            return JsonResponse({'success': False, 'error': 'Код истек или уже использован'})
        
        # Проверяем код
        if reset_code_obj.code != code:
            reset_code_obj.increment_attempts()
            attempts_left = 3 - reset_code_obj.attempts
            if attempts_left > 0:
                return JsonResponse({'success': False, 'error': f'Неверный код. Осталось попыток: {attempts_left}'})
            else:
                return JsonResponse({'success': False, 'error': 'Превышено максимальное количество попыток ввода кода'})
        
        # Код верный - генерируем новый пароль
        new_password = get_random_string(12)
        user.set_password(new_password)
        user.save()
        
        # Помечаем код как использованный
        reset_code_obj.is_used = True
        reset_code_obj.save()
        
        # Отправляем новые данные в Telegram
        if user.telegram_id:
            send_registration_details_sync(user.telegram_id, user.username, new_password)
        
        logger.info(f"Пароль успешно изменен для пользователя {user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Пароль успешно изменен. Новые данные отправлены в Telegram.',
            'redirect_url': reverse('users:login')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'})
    except Exception as e:
        logger.error(f"Ошибка при проверке кода восстановления: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Произошла ошибка при обработке запроса'})

@csrf_exempt
def password_reset_resend(request):
    """
    Повторная отправка кода восстановления
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    try:
        data = json.loads(request.body) if request.body else {}
        reset_code_id = data.get('reset_code_id')
        username = data.get('username', '').strip()
        
        if not reset_code_id or not username:
            return JsonResponse({'success': False, 'error': 'Не все данные предоставлены'})
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
        
        try:
            reset_code_obj = PasswordResetCode.objects.get(id=reset_code_id, user=user)
        except PasswordResetCode.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Код восстановления не найден'})
        
        # Проверяем возможность повторной отправки
        if not reset_code_obj.can_resend():
            if reset_code_obj.resend_count >= 3:
                return JsonResponse({'success': False, 'error': 'Превышено максимальное количество попыток отправки кода'})
            
            # Вычисляем время до следующей отправки
            time_since_last = timezone.now() - reset_code_obj.last_resend_at if reset_code_obj.last_resend_at else timezone.timedelta(seconds=0)
            seconds_remaining = max(0, 30 - int(time_since_last.total_seconds()))
            
            return JsonResponse({
                'success': False,
                'error': f'Повторная отправка возможна через {seconds_remaining} секунд',
                'seconds_remaining': seconds_remaining
            })
        
        # Генерируем новый код
        new_code = ''.join([str(get_random_string(1, allowed_chars='0123456789')) for _ in range(6)])
        reset_code_obj.code = new_code
        reset_code_obj.last_resend_at = timezone.now()
        reset_code_obj.resend_count += 1
        reset_code_obj.save()
        
        # Отправляем код в Telegram
        send_password_reset_code(user.telegram_id, new_code)
        
        logger.info(f"Код восстановления отправлен повторно для пользователя {user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Код восстановления отправлен повторно в Telegram.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'})
    except Exception as e:
        logger.error(f"Ошибка при повторной отправке кода: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Произошла ошибка при отправке кода'})
