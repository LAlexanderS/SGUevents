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
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.db.models.signals import m2m_changed

import logging
logger = logging.getLogger(__name__)

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
    time_end = models.TimeField(unique=False, blank=True, null=True, verbose_name='Время окончания')
    description = models.TextField(unique=False, blank=False, null=False, verbose_name='Описание')
    speakers = models.ManyToManyField(User, blank=True, related_name='speaker_online', verbose_name='Спикеры')
    member =  models.ManyToManyField(User, blank=True, related_name='member_online', verbose_name='Участники')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')
    platform = models.CharField(max_length=50, unique=False, blank=False, null=False, verbose_name='Платформа')
    link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка для подключения')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/online', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=True, related_name='admin_online', verbose_name="Соорганизаторы")
    documents = models.FileField(blank=True, null=True, verbose_name='Программа мероприятия')
    const_category = 'Онлайн'
    category = models.CharField(default=const_category, max_length=30, unique=False, blank=False, null=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='online_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    date_add = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    average_rating_cached = models.FloatField(default=0.0, verbose_name='Средний рейтинг', editable=False)
    save_media_to_disk = models.BooleanField(default=False, verbose_name='Сохранять медиафайлы на Яндекс Диск')
    yandex_disk_link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка на Яндекс Диск')
    users_chat_id = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='ID чата пользователей')
    users_chat_link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка на чат пользователей')
    support_chat_id = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='ID чата поддержки')

    related_online_events = models.ManyToManyField('Events_online', blank=True, related_name='related_to_online', verbose_name='Связанные онлайн мероприятия')
    related_offline_events = models.ManyToManyField('Events_offline', blank=True, related_name='related_to_offline', verbose_name='Связанные оффлайн мероприятия')
    related_attractions = models.ManyToManyField('events_cultural.Attractions', blank=True, related_name='related_to_online', verbose_name='Связанные достопримечательности')
    related_events_for_visiting = models.ManyToManyField('events_cultural.Events_for_visiting', blank=True, related_name='related_to_online', verbose_name='Связанные мероприятия для посещения')

    
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
        if self.date and self.date_end:
            if self.date > self.date_end:
                raise ValidationError({'date_end': 'Дата окончания должна быть позже даты начала'})
            elif self.date == self.date_end:
                if self.time_start and self.time_end:
                    if self.time_start > self.time_end:
                        raise ValidationError({'time_end': 'Время окончания должно быть позже времени начала'})
        else:
            raise ValidationError({'date': 'Проверьте корректность заполнения данных'})            
            
    def __str__(self):
        return self.name

    def display_id(self):
        return f'{self.id:05}'
    
    def formatted_date_range(self):
        if self.date and self.date_end: 
            if self.date != self.date_end:
                start_str = self.date.strftime('%d.%m.%Y')
                end_str = self.date_end.strftime('%d.%m.%Y')
                return f'{start_str}-{end_str}'
            else:
                return self.date.strftime('%d.%m.%Y')
        elif self.date and not self.date_end:
            return self.date.strftime('%d.%m.%Y')
        else:
            return f''
            
        
    def safe_description(self):
        from .utils import sanitize_html
        return sanitize_html(self.description)

    #Получение связных мероприятий
    def get_related_events(self):
        related_events = []
        
        # Добавляем связанные онлайн мероприятия
        related_events.extend(self.related_online_events.all())
        
        # Добавляем связанные оффлайн мероприятия
        related_events.extend(self.related_offline_events.all())
        
        # Добавляем связанные достопримечательности
        related_events.extend(self.related_attractions.all())
        
        # Добавляем связанные мероприятия для посещения
        related_events.extend(self.related_events_for_visiting.all())
        
        return related_events

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
        if self.date and self.time_end:
            combined_end_datetime = datetime.combine(self.date, self.time_end)
            self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        # Сначала сохраняем мероприятие (нужно для того, чтобы иметь ID объекта)
        super().save(*args, **kwargs)


# ====== Bidirectional sync for related fields of Events_online ======
@receiver(m2m_changed, sender=Events_online.related_online_events.through)
def sync_online_to_online(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    related_qs = Events_online.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_online_events.filter(pk=instance.pk).exists():
            related.related_online_events.add(instance)

@receiver(m2m_changed, sender=Events_online.related_offline_events.through)
def sync_online_to_offline(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    related_qs = Events_offline.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_online_events.filter(pk=instance.pk).exists():
            related.related_online_events.add(instance)

@receiver(m2m_changed, sender=Events_online.related_attractions.through)
def sync_online_to_attractions(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    # Import inside to avoid circular imports
    from events_cultural.models import Attractions
    related_qs = Attractions.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_online_events.filter(pk=instance.pk).exists():
            related.related_online_events.add(instance)

@receiver(m2m_changed, sender=Events_online.related_events_for_visiting.through)
def sync_online_to_visiting(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    from events_cultural.models import Events_for_visiting
    related_qs = Events_for_visiting.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_online_events.filter(pk=instance.pk).exists():
            related.related_online_events.add(instance)


class EventOnlineGallery(models.Model):
    event = models.ForeignKey('Events_online', on_delete=models.CASCADE, related_name='gallery', verbose_name='Мероприятие')
    image = models.ImageField(upload_to='event_online_gallery/', verbose_name='Фотография')

    class Meta:
        verbose_name = 'Фотографии онлайн мероприятий'
        verbose_name_plural = 'Галерея онлайн мероприятия'

    def __str__(self):
        return f'Фото для {self.event.name}'
    
class Events_offline(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, unique=False, blank=False, null=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False, verbose_name='URL')
    date = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата начала')
    date_end = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата окончания')
    time_start = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(unique=False, blank=True, null=True, verbose_name='Время окончания')
    description = models.TextField(unique=False, blank=False, null=False, verbose_name='Описание')
    speakers = models.ManyToManyField(User, blank=True, related_name='speaker_offline', verbose_name='Спикеры')
    member =  models.ManyToManyField(User, blank=True, related_name='member_offline', verbose_name='Участники')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')
    town = models.CharField(max_length=200, unique=False, blank=False, null=False, verbose_name='Город')
    street = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Улица')
    house = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Дом')
    cabinet = models.CharField(max_length=50, unique=False, blank=True, null=True, verbose_name='Кабинет')
    link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка к мероприятию')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/offline', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=True, related_name='admin_offline', verbose_name="Соорганизаторы")
    documents = models.FileField(blank=True, null=True, verbose_name='Программа мероприятия')
    const_category = 'Оффлайн'
    category = models.CharField(default=const_category, max_length=30, unique=False, blank=False, null=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='offline_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    date_add = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    average_rating_cached = models.FloatField(default=0.0, verbose_name='Средний рейтинг', editable=False)
    save_media_to_disk = models.BooleanField(default=False, verbose_name='Сохранять медиафайлы на Яндекс Диск')
    yandex_disk_link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка на Яндекс Диск')
    users_chat_id = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='ID чата пользователей')
    users_chat_link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка на чат пользователей')
    support_chat_id = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='ID чата поддержки')

        # Связанные мероприятия
    related_online_events = models.ManyToManyField('Events_online', blank=True, related_name='related_to_offline', verbose_name='Связанные онлайн мероприятия')
    related_offline_events = models.ManyToManyField('Events_offline', blank=True, related_name='related_to_offline_self', verbose_name='Связанные оффлайн мероприятия')
    related_attractions = models.ManyToManyField('events_cultural.Attractions', blank=True, related_name='related_to_offline', verbose_name='Связанные достопримечательности')
    related_events_for_visiting = models.ManyToManyField('events_cultural.Events_for_visiting', blank=True, related_name='related_to_offline', verbose_name='Связанные мероприятия для посещения')



    class Meta:
        db_table = 'Events_offline'
        verbose_name = 'Оффлайн мероприятие'
        verbose_name_plural = 'Оффлайн мероприятия'

    def clean(self):
        if self.date and self.date_end:
            if self.date > self.date_end:
                raise ValidationError({'date_end': 'Дата окончания должна быть позже даты начала'})
            elif self.date == self.date_end:
                if self.time_start > self.time_end:
                    raise ValidationError({'time_end': 'Время окончания должно быть позже времени начала'})
        else:
            raise ValidationError({'date': 'Проверьте корректность заполнения данных'})
         
    def __str__(self):
        return self.name

    def display_id(self):
        return f'{self.id:05}'

    def formatted_date_range(self):
        if self.date_end and self.date != self.date_end:
            start_str = self.date.strftime('%d.%m.%Y')
            end_str = self.date_end.strftime('%d.%m.%Y')
            return f'{start_str} - {end_str}'
        else:
            return self.date.strftime('%d.%m.%Y')
    
    def formatted_date_2(self):
        if self.date_end and self.date != self.date_end:
            start_str = self.date.strftime('%d.%m.%Y')
            end_str = self.date_end.strftime('%d.%m.%Y')
            return f'{start_str} - {end_str}'
        else:
            return self.date.strftime('%d.%m.%Y')
        
    def safe_description(self):
        from .utils import sanitize_html
        return sanitize_html(self.description)


    def get_related_events(self):
        related_events = []
        
        # Добавляем связанные онлайн мероприятия
        related_events.extend(self.related_online_events.all())
        
        # Добавляем связанные оффлайн мероприятия
        related_events.extend(self.related_offline_events.all())
        
        # Добавляем связанные достопримечательности
        related_events.extend(self.related_attractions.all())
        
        # Добавляем связанные мероприятия для посещения
        related_events.extend(self.related_events_for_visiting.all())
        
        return related_events
        
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


# ====== Bidirectional sync for related fields of Events_offline ======
@receiver(m2m_changed, sender=Events_offline.related_offline_events.through)
def sync_offline_to_offline(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    related_qs = Events_offline.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_offline_events.filter(pk=instance.pk).exists():
            related.related_offline_events.add(instance)

@receiver(m2m_changed, sender=Events_offline.related_online_events.through)
def sync_offline_to_online(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    related_qs = Events_online.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_offline_events.filter(pk=instance.pk).exists():
            related.related_offline_events.add(instance)

@receiver(m2m_changed, sender=Events_offline.related_attractions.through)
def sync_offline_to_attractions(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    from events_cultural.models import Attractions
    related_qs = Attractions.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_offline_events.filter(pk=instance.pk).exists():
            related.related_offline_events.add(instance)

@receiver(m2m_changed, sender=Events_offline.related_events_for_visiting.through)
def sync_offline_to_visiting(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'post_add' or reverse:
        return
    if not pk_set:
        return
    from events_cultural.models import Events_for_visiting
    related_qs = Events_for_visiting.objects.filter(pk__in=pk_set)
    for related in related_qs:
        if not related.related_offline_events.filter(pk=instance.pk).exists():
            related.related_offline_events.add(instance)


class EventOfflineGallery(models.Model):
    event = models.ForeignKey('Events_offline', on_delete=models.CASCADE, related_name='gallery', verbose_name='Мероприятие')
    image = models.ImageField(upload_to='event_offline_gallery/', verbose_name='Фотография')

    class Meta:
        verbose_name = 'Фотографии оффлайн мероприятий'
        verbose_name_plural = 'Галерея оффлайн мероприятия'

    def __str__(self):
        return f'Фото для {self.event.name}'

class EventOfflineCheckList(models.Model):
        event = models.ForeignKey(
            'Events_offline',
            on_delete=models.CASCADE,
            related_name='checklist',
            verbose_name='Мероприятие'
        )
        # task_name = models.CharField(max_length=255, verbose_name='Наименование задачи')
        task_name = models.ForeignKey(
            'DefaultTasks',
            on_delete=models.CASCADE,
            null=True,
            blank=True,
            verbose_name='Наименование задачи'
        )
        responsible = models.ForeignKey(
            User,
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            verbose_name='Ответственный'
        )
        planned_date = models.DateField(null=True, blank=True, verbose_name='Плановая дата')
        actual_date = models.DateField(null=True, blank=True, verbose_name='Дата исполнения')
        completed = models.BooleanField(default=False, verbose_name='Исполнено')

        class Meta:
            verbose_name = 'Этап подготовки'
            verbose_name_plural = 'Чек-лист мероприятия'
            ordering = ['planned_date']

        def __str__(self):
            return f"{self.task_name} ({'✓' if self.completed else '—'})"


class DefaultTasks(models.Model):
    name = models.CharField(max_length=512, verbose_name="Задача")

    class Meta:
        verbose_name = 'Задачи'

    def __str__(self):
        return f"{self.name}"

# @receiver(post_save, sender=EventOfflineCheckList)
# def create_default_checklist(sender, instance, created, **kwargs):
    
#     DEFAULT_TASKS = [
#         "Определение количества и состава участников",
#         "Составление сметы мероприятия",
#         "Сбор регистрационной информации (Дата, время прилета, рейс, гостиница, необходимость трансфера)",
#         "Составление заявок на проход на территорию",
#         "Составление маршрута транспорта",
#         "Составление заявок на транспорт",
#         "Составление заявок на разрешение фото-, видеосъемки",
#         "Составление культурной пограммы",
#         "Сбор информации по участию в культурной программе (возможно как доп информация в регистрационной карточке)",
#         "Оформление приветственной открытки",
#         "Оформление приветственного пакета",
#         "Оформление бэйджей",
#         "Оформление стоек с ФИО на столы",
#         "Оформление раздаточного материала (рабочая тетрадь)",
#         "Оформление макета баннера",
#         "Согласование сопровождения фото-, видеосъемки",
#         "Согласование рассадки гостей в залах",
#         "Подготовка презентационного материала",
#         "Закупка сувенирной (брендированной) продукции"
#     ]
#     for task in DEFAULT_TASKS:
#         EventOfflineCheckList.objects.create(event=instance, task_name=task)

class EventLogistics(models.Model):
    """
    Модель для хранения логистической информации по участию
    пользователя в офлайн-мероприятии.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    event = models.ForeignKey(
        Events_offline,
        on_delete=models.CASCADE,
        verbose_name="Офлайн-мероприятие"
    )

    # Информация о прилете
    arrival_datetime = models.DateTimeField(
        verbose_name="Дата и время прилета",
        null=True, blank=True
    )
    arrival_flight_number = models.CharField(
        max_length=20,
        verbose_name="Рейс прилета",
        blank=True
    )
    arrival_airport = models.CharField(
        max_length=100,
        verbose_name="Аэропорт прилета",
        blank=True
    )

    # Информация об отлёте
    departure_datetime = models.DateTimeField(
        verbose_name="Дата и время отлёта",
        null=True, blank=True
    )
    departure_flight_number = models.CharField(
        max_length=20,
        verbose_name="Рейс отлёта",
        blank=True
    )
    departure_airport = models.CharField(
        max_length=100,
        verbose_name="Аэропорт отлёта",
        blank=True
    )

    # Дополнительная информация
    transfer_needed = models.BooleanField(
        default=False,
        verbose_name="Нужен трансфер"
    )
    hotel_details = models.TextField(
        verbose_name="Гостиница проживания",
        blank=True,
        help_text="Название, адрес, номер брони и т.д."
    )
    meeting_person = models.TextField(
        verbose_name="Встречающий",
        blank=True,
        help_text="ФИО встречающего"
    )

    class Meta:
        verbose_name = "Логистику по мероприятию"
        verbose_name_plural = "Логистика по мероприятиям"
        # Гарантируем, что для одной пары пользователь-мероприятие есть только одна запись
        unique_together = ('user', 'event')
        ordering = ['event__start_datetime', 'user__last_name']

    def clean(self):
        if self.arrival_datetime and self.departure_datetime:
            if self.arrival_datetime >= self.departure_datetime:
                raise ValidationError({'departure_datetime': 'Дата улёта должна быть позже даты прилёта'})
    

    def save(self, *args, **kwargs):
        self.clean()

        super(EventLogistics, self).save(*args, **kwargs)


    def __str__(self):
        return f"Логистика для {self.user} на {self.event.name}"

