import uuid
from django.db import models
from datetime import datetime
from django.utils.timezone import make_aware, get_default_timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from users.models import Department, User
from django.utils import timezone
from pytz import timezone as pytz_timezone

class Attractions(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, blank=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, verbose_name='URL')
    date = models.DateField(max_length=10, blank=False, verbose_name='Дата')
    time_start = models.TimeField(blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(blank=False, null=False, verbose_name='Время окончания')
    description = models.TextField(blank=False, null=False, verbose_name='Описание')
    town = models.CharField(max_length=200, blank=False, verbose_name='Город')
    street = models.CharField(max_length=100, blank=False, verbose_name='Улица')
    link = models.URLField(blank=False, verbose_name='Ссылка')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/offline', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=False, related_name='admin_attractions', verbose_name="Администратор")
    rating = models.DecimalField(default=0.00, max_digits=4, decimal_places=2, blank=False, verbose_name='Рейтинг 1-10')
    documents = models.FileField(blank=True, null=True, verbose_name='Документы')
    const_category = 'Достопримечательности'
    category = models.CharField(default=const_category, max_length=30, blank=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='attraction_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')


    class Meta:
        db_table = 'attractions'
        verbose_name = 'Достопримечательности'
        verbose_name_plural = 'Достопримечательности'

    def __str__(self):
        return self.name

    def display_id(self):
        return f'{self.id:05}'

    def save(self, *args, **kwargs):
        self._current_user = kwargs.pop('user', None)  # Сохраняем пользователя для использования в сигнале
        combined_start_datetime = datetime.combine(self.date, self.time_start)
        self.start_datetime = make_aware(combined_start_datetime, timezone=get_default_timezone())

        combined_end_datetime = datetime.combine(self.date, self.time_end)
        self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        super(Attractions, self).save(*args, **kwargs)

class Events_for_visiting(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, unique=False, blank=False, null=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False, verbose_name='URL')
    date = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата')
    time_start = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время окончания')
    description = models.TextField(unique=False, blank=False, null=False, verbose_name='Описание')
    member =  models.ManyToManyField(User, blank=True, related_name='member_visiting', verbose_name='Участники')
    town = models.CharField(max_length=200, unique=False, blank=False, null=False, verbose_name='Город')
    street = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Улица')
    link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/offline', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=False, related_name='admin_visiting', verbose_name="Администратор")
    place_limit = models.IntegerField(unique=False, blank=False, null=False, verbose_name='Количество мест')
    place_free = models.IntegerField(unique=False, blank=False, null=False, verbose_name='Количество свободных мест')
    documents = models.FileField(blank=True, null=True, verbose_name='Документы')
    const_category = 'Доступные к посещению'
    category = models.CharField(default=const_category, max_length=30, unique=False, blank=False, null=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='visiting_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')


    class Meta:
        db_table = 'Events_for_visiting'
        verbose_name = 'Доступные к посещению'
        verbose_name_plural = 'Доступные к посещению'

    def __str__(self):
        return self.name

    def display_id(self):
        return f'{self.id:05}'

    def save(self, *args, **kwargs):
        self._current_user = kwargs.pop('user', None)  # Сохраняем пользователя для использования в сигнале
        combined_start_datetime = datetime.combine(self.date, self.time_start)
        self.start_datetime = make_aware(combined_start_datetime, timezone=get_default_timezone())

        combined_end_datetime = datetime.combine(self.date, self.time_end)
        self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        super(Events_for_visiting, self).save(*args, **kwargs)




