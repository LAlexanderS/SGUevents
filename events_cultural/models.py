import uuid
from django.db import models
from datetime import datetime
from django.utils.timezone import make_aware, get_default_timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from users.models import Department, User
from django.utils import timezone
from pytz import timezone as pytz_timezone
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Attractions(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, blank=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, verbose_name='URL')
    date = models.DateField(max_length=10, blank=False, verbose_name='Дата')
    date_end = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата окончания')
    time_start = models.TimeField(blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(blank=True, null=True, verbose_name='Время окончания')
    description = models.TextField(blank=False, null=False, verbose_name='Описание')
    link = models.URLField(blank=False, verbose_name='Ссылка на достопримечательность')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/offline', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=True, related_name='admin_attractions', verbose_name="Администратор")
    rating = models.DecimalField(default=0.00, max_digits=4, decimal_places=2, blank=False, verbose_name='Рейтинг 1-10')
    documents = models.FileField(blank=True, null=True, verbose_name='Документы')
    const_category = 'Достопримечательности'
    category = models.CharField(default=const_category, max_length=30, blank=False, verbose_name='Тип мероприятия')
    reviews = GenericRelation('bookmarks.Review', related_query_name='attraction_reviews')
    start_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время начала')
    end_datetime = models.DateTimeField(editable=False, null=True, blank=True, verbose_name='Дата и время окончания')
    secret = models.ManyToManyField(Department, blank=True, verbose_name='Ключ для мероприятия')
    tags = models.CharField(max_length=100, unique=False, blank=True, null=True, verbose_name='Теги')
    house = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Дом')
    town = models.CharField(max_length=200, blank=False, verbose_name='Город')
    street = models.CharField(max_length=100, blank=False, verbose_name='Улица')
    member =  models.ManyToManyField(User, blank=True, related_name='member_attractions', verbose_name='Участники')
    date_add = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        db_table = 'attractions'
        verbose_name = 'Достопримечательности'
        verbose_name_plural = 'Достопримечательности'

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
    
    def formatted_date_range(self):
        if self.date_end and self.date != self.date_end:
            start_str = self.date.strftime('%d.%m')
            end_str = self.date_end.strftime('%d.%m')
            return f'{start_str} - {end_str}'
        else:
            return self.date.strftime('%d.%m.%Y')

    def save(self, *args, **kwargs):
        self.clean()

        local_timezone = pytz_timezone('Asia/Novosibirsk')
        self.date_submitted = timezone.now().astimezone(local_timezone)

        if not self.slug.startswith('att-'):
            self.slug = f'att-{slugify(self.slug)}'

        self._current_user = kwargs.pop('user', None)  # Сохраняем пользователя для использования в сигнале
        combined_start_datetime = datetime.combine(self.date, self.time_start)
        self.start_datetime = make_aware(combined_start_datetime, timezone=get_default_timezone())

        combined_end_datetime = datetime.combine(self.date, self.time_end)
        self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        super(Attractions, self).save(*args, **kwargs)

class AttractionsGallery(models.Model):
    event = models.ForeignKey('Attractions', on_delete=models.CASCADE, related_name='gallery', verbose_name='Мероприятие')
    image = models.ImageField(upload_to='attractions_gallery/', verbose_name='Фотография')

    class Meta:
        verbose_name = 'Фотография мероприятия'
        verbose_name_plural = 'Галерея мероприятия'

    def __str__(self):
        return f'Фото для {self.event.name}'

class Events_for_visiting(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Уникальный ID')
    name = models.CharField(max_length=150, unique=False, blank=False, null=False, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False, verbose_name='URL')
    date = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата начала')
    date_end = models.DateField(max_length=10, unique=False, blank=False, null=False, verbose_name='Дата окончания')
    time_start = models.TimeField(unique=False, blank=False, null=False, verbose_name='Время начала')
    time_end = models.TimeField(unique=False, blank=True, null=True, verbose_name='Время окончания')
    description = models.TextField(unique=False, blank=False, null=False, verbose_name='Описание')
    member =  models.ManyToManyField(User, blank=True, related_name='member_visiting', verbose_name='Участники')
    town = models.CharField(max_length=200, unique=False, blank=False, null=False, verbose_name='Город')
    street = models.CharField(max_length=100, unique=False, blank=False, null=False, verbose_name='Улица')
    link = models.URLField(unique=False, blank=True, null=True, verbose_name='Ссылка на место проведения')
    qr = models.FileField(blank=True, null=True, verbose_name='QR-код')
    image = models.ImageField(upload_to='events_available_images/offline', blank=True, null=True, verbose_name='Изображение')
    events_admin = models.ManyToManyField(User, limit_choices_to={'is_staff': True}, blank=True, related_name='admin_visiting', verbose_name="Администратор")
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
    date_add = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        db_table = 'Events_for_visiting'
        verbose_name = 'Доступные к посещению'
        verbose_name_plural = 'Доступные к посещению'
    
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
    
    def formatted_date_range(self):
        if self.date_end and self.date != self.date_end:
            start_str = self.date.strftime('%d.%m')
            end_str = self.date_end.strftime('%d.%m')
            return f'{start_str} - {end_str}'
        else:
            return self.date.strftime('%d.%m.%Y')

    def save(self, *args, **kwargs):
        self.clean()

        local_timezone = pytz_timezone('Asia/Novosibirsk')
        self.date_submitted = timezone.now().astimezone(local_timezone)

        if not self.slug.startswith('vis-'):
            self.slug = f'vis-{slugify(self.slug)}'

        self._current_user = kwargs.pop('user', None)  # Сохраняем пользователя для использования в сигнале
        combined_start_datetime = datetime.combine(self.date, self.time_start)
        self.start_datetime = make_aware(combined_start_datetime, timezone=get_default_timezone())

        combined_end_datetime = datetime.combine(self.date, self.time_end)
        self.end_datetime = make_aware(combined_end_datetime, timezone=get_default_timezone())

        super(Events_for_visiting, self).save(*args, **kwargs)


class Events_for_visitingGallery(models.Model):
    event = models.ForeignKey('Events_for_visiting', on_delete=models.CASCADE, related_name='gallery', verbose_name='Мероприятие')
    image = models.ImageField(upload_to='Events_for_visiting_gallery/', verbose_name='Фотография')

    class Meta:
        verbose_name = 'Фотография мероприятия'
        verbose_name_plural = 'Галерея мероприятия'

    def __str__(self):
        return f'Фото для {self.event.name}'

# @receiver(m2m_changed, sender=Events_for_visiting.member.through)
# def update_place_free(sender, instance, action, **kwargs):
#     print(f'1 instance.place_limit: {instance.place_limit}')
#     print(f'2 instance.member.count(): {instance.member.count()}')
    
#     if action == 'post_add':
#         instance.place_free = instance.place_limit - instance.member.count()
#         instance.save()
#     elif action == 'post_remove':
#         instance.place_free = instance.place_limit - instance.member.count()
#         instance.save()
#     print(f'3 instance.place_free {instance.place_free}')




