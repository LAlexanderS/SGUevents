import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.crypto import get_random_string
from transliterate import translit, exceptions
import re


class Department(models.Model):
    department_id = models.CharField(max_length=50, unique=True, verbose_name='ID отдела')
    department_name = models.CharField(max_length=100, verbose_name='Название отдела')

    def __str__(self):
        return self.department_name

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

class CustomUserManager(BaseUserManager):
    def transliterate_username(self, last_name, first_name, middle_name=''):
        transliterated = ''
        try:
            transliterated = translit(last_name, 'ru', reversed=True)
            transliterated += translit(first_name[0], 'ru', reversed=True) if first_name else ''
            transliterated += translit(middle_name[0], 'ru', reversed=True) if middle_name else ''
            transliterated = re.sub(r"'", "", transliterated)
        except exceptions.LanguageDetectionError:
            transliterated = last_name + (first_name[0] if first_name else '') + (middle_name[0] if middle_name else '')

        base_username = transliterated
        counter = 1
        while self.model.objects.filter(username=transliterated).exists():
            transliterated = f"{base_username}{counter}"
            counter += 1

        return transliterated

    def create_user(self, email=None, password=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
        password = get_random_string(8) if password is None else password
        first_name = extra_fields.pop('first_name', '')
        last_name = extra_fields.pop('last_name', '')
        middle_name = extra_fields.pop('middle_name', '')
        department = extra_fields.pop('department', None)
        telegram_id = extra_fields.pop('telegram_id', None)

        username = extra_fields.pop('username', None) or self.transliterate_username(last_name, first_name, middle_name)

        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            department=department,
            telegram_id=telegram_id,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')
        extra_fields.setdefault('department', Department.objects.get_or_create(department_id='1', defaults={'department_name': 'Administration'})[0])
        extra_fields.setdefault('telegram_id', 'default_telegram_id')

        if not email:
            raise ValueError('The Email must be set for superuser')
        if password is None:
            raise ValueError('Superuser must have a password')

        email = self.normalize_email(email)
        user = self.create_user(email, password, **extra_fields)

        user.save(using=self._db)
        return user

class User(AbstractUser):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Отчество')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name='Отдел')
    telegram_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='Telegram ID')
    email = models.EmailField('email address', blank=True, null=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class AdminRightRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    reason = models.TextField(verbose_name="Основание")
    status = models.CharField(max_length=20, choices=[('pending', 'Ожидает'), ('granted', 'Предоставлено'), ('denied', 'Отказано')], default='pending', verbose_name="Статус")
    response = models.TextField(blank=True, null=True, verbose_name="Ответ")

    def __str__(self):
        return f"{self.user.username} - {self.status}"

    class Meta:
        verbose_name = "Запрос на админские права"
        verbose_name_plural = "Запросы на админские права"

class SupportRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    question = models.TextField(verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_resolved = models.BooleanField(default=False, verbose_name="Решен")

    def __str__(self):
        return f"Запрос от {self.user.username} - {self.created_at}"

    class Meta:
        verbose_name = "Запрос в техподдержку"
        verbose_name_plural = "Запросы в техподдержку"

