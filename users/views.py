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

from .forms import RegistrationForm
from .models import Department, AdminRightRequest
from .telegram_utils import send_registration_details_sync, send_password_change_details_sync
from .telegram_utils import send_message_to_admin, send_confirmation_to_user
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from aiogram import types
from asgiref.sync import async_to_sync
from bot.main import handle_webhook

User = get_user_model()
logger = logging.getLogger(__name__)

DEV_BOT_NAME = os.getenv('DEV_BOT_NAME')
BOT_NAME = os.getenv('BOT_NAME')

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

            if new_user.telegram_id:
                send_registration_details_sync(new_user.telegram_id, new_user.username, generated_password)

            return redirect('users:login')
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else 'EventsSGUbot',
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
            return redirect('main:index')
        else:
            messages.error(request, "Неверный логин или пароль.")
    context = {
        'telegram_bot_username': DEV_BOT_NAME if os.getenv('DJANGO_ENV') == 'development' else BOT_NAME
    }
    return render(request, 'users/login.html', context)

@csrf_exempt
def telegram_auth(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        telegram_id = data.get('telegram_id')
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user:
            auth_login(request, user)
            request.session['login_method'] = 'Через Telegram'
            return JsonResponse({'success': True, 'redirect_url': '/'})
        else:
            return JsonResponse({'success': False, 'error': 'У вас нет учетной записи.\nПожалуйста, пройдите регистрацию.', 'redirect_url': '/users/register'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
@login_required
def change_password(request):
    if request.method == 'POST' and request.user.telegram_id:
        new_password = get_random_string(8)
        request.user.set_password(new_password)
        request.user.save()
        send_password_change_details_sync(request.user.telegram_id, request.user.username, new_password)
        logger.info("Password changed, logging out user and redirecting to login page")
        logout(request)
        return JsonResponse({'success': True, 'message': 'Пароль успешно изменен. Новый пароль отправлен в Telegram.'})
    else:
        logger.error("Failed to change password: Access denied or missing telegram_id")
        return JsonResponse({'success': False, 'error': 'Access denied.'})

@csrf_exempt
@login_required
def request_admin_rights(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            justification = data.get('reason', '')
            user_full_name = f"{request.user.last_name} {request.user.first_name} {' ' + request.user.middle_name if request.user.middle_name else ''}".strip()
            message = f"Запрос на админские права от {user_full_name}: {justification}"

            # Создание новой записи запроса на админские права
            new_request = AdminRightRequest(user=request.user, reason=justification)
            new_request.save()

            # Отправка сообщения администратору
            send_message_to_admin(request.user.telegram_id, message)
            # Уведомление пользователя о том, что запрос отправлен
            send_confirmation_to_user(request.user.telegram_id)

            return JsonResponse({'success': True,
                                 'message': 'Запрос на админские права отправлен администратору и зарегистрирован в системе.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Ошибка в формате данных.'})
    return JsonResponse({'success': False, 'error': 'Недопустимый запрос.'})

@login_required
def profile(request):
    user = request.user
    login_method = request.session.get('login_method', 'Неизвестный способ входа')
    department_name = user.department.department_name if user.department else 'Не указан'
    return render(request, 'users/profile.html', {'user': user, 'login_method': login_method, 'department_name': department_name})

@login_required
def logout(request):
    auth.logout(request)
    return redirect(reverse('main:index'))

def general(request):
    return render(request, 'main/index.html')

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        return async_to_sync(handle_webhook)(request)  # Используем async_to_sync для вызова асинхронной функции
    return JsonResponse({"error": "Invalid request method"}, status=400)
