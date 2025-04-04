from django.contrib.auth.models import Group
import uuid
from django.db import models
from datetime import datetime
from django.utils.timezone import make_aware, get_default_timezone
from django.contrib.contenttypes.fields import GenericRelation
from users.models import Department, User
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from pytz import timezone as pytz_timezone
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class MediaFile(models.Model):
    message_id = models.CharField(max_length=100, verbose_name='ID сообщения')
    chat_id = models.CharField(max_length=100, verbose_name='ID чата')
    file_path = models.CharField(max_length=500, verbose_name='Путь к файлу на Яндекс.Диске')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    is_deleted = models.BooleanField(default=False, verbose_name='Удален')
    celery_task_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='ID задачи Celery')

    class Meta:
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'
        indexes = [
            models.Index(fields=['message_id', 'chat_id']),
        ]

    def __str__(self):
        return f"Файл {self.file_path} из чата {self.chat_id}"

class Events_online(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, unique=False, blank=False, null=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False, verbose_name='URL')
    date = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата начала')
    date_end = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата окончания')
    time_start = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время окончания')
    description = models.TextField(unique=False, blank=False, null=False, verbose_name='Описание')
    speakers = models.ManyToManyField(User, blank=True, related_name='speaker_online', verbose_name='Спикеры')
    member =  models.ManyToManyField(User, blank=True, related_name='member_online', verbose_name='Участники')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')
    platform = models.CharField(max_length=50, unique=False, blank=False, null=False, verbose_name='Платформа')
    link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка для подключения')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/online', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=True, related_name='admin_online', verbose_name="Администратор")
    documents = models.FileField(blank=True, null=True, verbose_name='Документы')
    const_category = 'Онлайн'
    category = models.CharField(default=const_category, max_length=30, unique=False, blank=False, null=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='online_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    date_add = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    # admin_groups = models.ManyToManyField(Group, blank=True, related_name='event_admin_groups', verbose_name="Администраторы (группы)")


    class Meta:
        db_table = 'Events_online'
        verbose_name = 'Онлайн мероприятие'
        verbose_name_plural = 'Онлайн мероприятия'
        indexes = [
            GinIndex(fields=["name"], opclasses=["gin_trgm_ops"], name="name_trgm_idx"),
            GinIndex(fields=["description"], opclasses=["gin_trgm_ops"], name="description_trgm_idx"),
        ]

    def clean(self):
        if self.date > self.date_end:
            raise ValidationError({'date_end': 'Дата окончания должна быть позже даты начала'})
        elif self.date == self.date_end:
            if self.time_start > self.time_end:
                raise ValidationError({'time_end': 'Время окончания должно быть позже времени начала'})
            
    def __str__(self):
        return self.name

    def display_id(self):
        return f'{self.id:05}'

    def save(self, *args, **kwargs):
        self.clean()

    # Сохраняем временную зону и дату для событий
        local_timezone = pytz_timezone('Asia/Novosibirsk')
        self.date_submitted = timezone.now().astimezone(local_timezone)

        if not self.slug.startswith('onl-'):
            self.slug = f'onl-{slugify(self.slug)}'

        self._current_user = kwargs.pop('user', None)  # Сохраняем пользователя для использования в сигнале
        combined_start_datetime = datetime.combine(self.date, self.time_start)
        self.start_datetime = make_aware(combined_start_datetime, timezone=get_default_timezone())

        combined_end_datetime = datetime.combine(self.date, self.time_end)
        self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        # Сначала сохраняем мероприятие (нужно для того, чтобы иметь ID объекта)
        super().save(*args, **kwargs)

class EventOnlineGallery(models.Model):
    event = models.ForeignKey('Events_online', on_delete=models.CASCADE, related_name='gallery', verbose_name='Мероприятие')
    image = models.ImageField(upload_to='event_online_gallery/', verbose_name='Фотография')

    class Meta:
        verbose_name = 'Фотография мероприятия'
        verbose_name_plural = 'Галерея мероприятия'

    def __str__(self):
        return f'Фото для {self.event.name}'
    
class Events_offline(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, unique=False, blank=False, null=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False, verbose_name='URL')
    date = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата начала')
    date_end = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата окончания')
    time_start = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время окончания')
    description = models.TextField(unique=False, blank=False, null=False, verbose_name='Описание')
    speakers = models.ManyToManyField(User, blank=True, related_name='speaker_offline', verbose_name='Спикеры')
    member =  models.ManyToManyField(User, blank=True, related_name='member_offline', verbose_name='Участники')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')
    town = models.CharField(max_length=200, unique=False, blank=False, null=False, verbose_name='Город')
    street = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Улица')
    house = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Дом')
    cabinet = models.CharField(max_length=50, unique=False, blank=True, null=True, verbose_name='Кабинет')
    link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка к мероприятию')
    yandex_disk_link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка на Яндекс Диск')
    users_chat_id = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='ID чата пользователей')
    save_media_to_disk = models.BooleanField(default=False, verbose_name='Сохранять медиафайлы на Яндекс Диск')
    support_chat_id = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='ID чата поддержки')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/offline', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=True, related_name='admin_offline', verbose_name="Администратор")
    documents = models.FileField(blank=True, null=True, verbose_name='Документы')
    const_category = 'Оффлайн'
    category = models.CharField(default=const_category, max_length=30, unique=False, blank=False, null=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='offline_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    date_add = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        db_table = 'Events_offline'
        verbose_name = 'Оффлайн мероприятие'
        verbose_name_plural = 'Оффлайн мероприятия'

    def clean(self):
        if self.date > self.date_end:
            raise ValidationError({'date_end': 'Дата окончания должна быть позже даты начала'})
        elif self.date == self.date_end:
            if self.time_start > self.time_end:
                raise ValidationError({'time_end': 'Время окончания должно быть позже времени начала'})
            
    def __str__(self):
        return self.name

    def display_id(self):
        return f'{self.id:05}'

    def save(self, *args, **kwargs):
        self.clean()

        local_timezone = pytz_timezone('Asia/Novosibirsk')
        self.date_submitted = timezone.now().astimezone(local_timezone)
        
        if not self.slug.startswith('off-'):
            self.slug = f'off-{slugify(self.slug)}'

        self._current_user = kwargs.pop('user', None)  # Сохраняем пользователя для использования в сигнале
        combined_start_datetime = datetime.combine(self.date, self.time_start)
        self.start_datetime = make_aware(combined_start_datetime, timezone=get_default_timezone())

        combined_end_datetime = datetime.combine(self.date, self.time_end)
        self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        super(Events_offline, self).save(*args, **kwargs)

class EventOfflineGallery(models.Model):
    event = models.ForeignKey('Events_offline', on_delete=models.CASCADE, related_name='gallery', verbose_name='Мероприятие')
    image = models.ImageField(upload_to='event_offline_gallery/', verbose_name='Фотография')

    class Meta:
        verbose_name = 'Фотография мероприятия'
        verbose_name_plural = 'Галерея мероприятия'

    def __str__(self):
        return f'Фото для {self.event.name}'
