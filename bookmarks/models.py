import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils.timezone import make_aware, get_default_timezone
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from users.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from users.telegram_utils import send_message_to_user_with_toggle_button, send_custom_notification_with_toggle
import logging
from django.utils import timezone
from pytz import timezone as pytz_timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg


logger = logging.getLogger(__name__)

class Favorite(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, default=1, verbose_name="Пользователь")
    online = models.ForeignKey(to=Events_online, on_delete=models.CASCADE, verbose_name="Онлайн", null=True, blank=True)
    offline = models.ForeignKey(to=Events_offline, on_delete=models.CASCADE, verbose_name="Оффлайн", null=True, blank=True)
    attractions = models.ForeignKey(to=Attractions, on_delete=models.CASCADE, verbose_name="Достопримечательности", null=True, blank=True)
    for_visiting = models.ForeignKey(to=Events_for_visiting, on_delete=models.CASCADE, verbose_name="Доступные для посещения", null=True, blank=True)
    created_timestamp = models.DateTimeField(verbose_name="Дата добавления")

    def save(self, *args, **kwargs):
        if not self.created_timestamp:
            local_timezone = pytz_timezone('Asia/Novosibirsk')
            self.created_timestamp = timezone.now().astimezone(local_timezone)
        super(Favorite, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Избранные"
        verbose_name_plural = "Избранные"

    def __str__(self):
        try:
            return f'Избранные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.online.name} | Тип {self.online.category}'
        except:
            try:
                return f'Избранные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.offline.name} | Тип {self.offline.category}'
            except:
                try:
                    return f'Избранные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.attractions.name} | Тип {self.attractions.category}'
                except:
                    return f'Избранные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.for_visiting.name} | Тип {self.for_visiting.category}'


class Registered(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name="Пользователь")
    online = models.ForeignKey(to=Events_online, on_delete=models.CASCADE, verbose_name="Онлайн", null=True, blank=True)
    offline = models.ForeignKey(to=Events_offline, on_delete=models.CASCADE, verbose_name="Оффлайн", null=True, blank=True)
    attractions = models.ForeignKey(to=Attractions, on_delete=models.CASCADE, verbose_name="Достопримечательности", null=True, blank=True)
    for_visiting = models.ForeignKey(to=Events_for_visiting, on_delete=models.CASCADE, verbose_name="Доступные для посещения", null=True, blank=True)
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    notifications_enabled = models.BooleanField(default=True, verbose_name="Уведомления включены")

    def save(self, *args, **kwargs):
        if not self.created_timestamp:
            local_timezone = pytz_timezone('Asia/Novosibirsk')
            self.created_timestamp = timezone.now().astimezone(local_timezone)
        super(Registered, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Зарегистрированные"
        verbose_name_plural = "Зарегистрированные"

    def __str__(self):
        try:
            return f'Зарегистрированные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.online.name} | Тип {self.online.category}'
        except:
            try:
                return f'Зарегистрированные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.offline.name} | Тип {self.offline.category}'
            except:
                try:
                    return f'Зарегистрированные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.attractions.name} | Тип {self.attractions.category}'
                except:
                    return f'Зарегистрированные | {self.user.last_name} {self.user.first_name} {self.user.middle_name} | Мероприятие {self.for_visiting.name} | Тип {self.for_visiting.category}'


from django.utils import timezone
from pytz import timezone as pytz_timezone

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    event = GenericForeignKey('content_type', 'object_id')
    comment = models.TextField(verbose_name='Комментарий')
    rating = models.PositiveIntegerField(verbose_name='Оценка', choices=[
        (1, '1 звезда'),
        (2, '2 звезды'),
        (3, '3 звезды'),
        (4, '4 звезды'),
        (5, '5 звезд')
    ], null=True, blank=True) 
    date_submitted = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')

    def save(self, *args, **kwargs):
        local_timezone = pytz_timezone('Asia/Novosibirsk')
        self.date_submitted = timezone.now().astimezone(local_timezone)
        super(Review, self).save(*args, **kwargs)

            # Обновить рейтинг после сохранения
        content_type = ContentType.objects.get_for_model(self.event)
        model_class = content_type.model_class()
        if hasattr(self.event, 'reviews'):
            avg = Review.objects.filter(content_type=content_type, object_id=self.object_id, rating__isnull=False).aggregate(Avg('rating'))['rating__avg'] or 0
            model_class.objects.filter(pk=self.object_id).update(average_rating_cached=round(avg, 1))

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.formatted_date()} Отзыв от {self.user.username} на {self.event}'

    def formatted_date(self):
        local_timezone = pytz_timezone('Asia/Novosibirsk')
        return self.date_submitted.astimezone(local_timezone).strftime("%d.%m.%Y %H:%M")



@receiver(post_save, sender=Registered)
def notify_user_on_registration(sender, instance, created, **kwargs):
    if created:
        event_name = instance.online.name if instance.online else (
            instance.offline.name if instance.offline else (
                instance.attractions.name if instance.attractions else instance.for_visiting.name))
        message = f"\U00002705 Вы зарегистрировались на мероприятие: {event_name}."
        user_telegram_id = instance.user.telegram_id

        # Проверка наличия Telegram ID
        if user_telegram_id:
            logger.info(f"Отправка сообщения о регистрации пользователю {instance.user.username} с telegram_id: {user_telegram_id}")
            send_message_to_user_with_toggle_button(user_telegram_id, message, instance.id, instance.notifications_enabled)
        else:
            logger.warning(f"У пользователя {instance.user.username} нет telegram_id, пропускаем отправку.")



def send_update_notification(user, event, new_start_time):
    message = f"Изменились детали мероприятия: дата и время начала изменилось на {new_start_time}."
    user_telegram_id = user.telegram_id

    # Проверка наличия и корректности Telegram ID
    if user_telegram_id and len(user_telegram_id) > 0:
        try:
            logger.info(f"Пробуем отправить уведомление пользователю {user.username} с telegram_id: {user_telegram_id}")
            response = send_custom_notification_with_toggle(user_telegram_id, message, event.unique_id, True)
            if not response.ok:
                logger.error(f"Ошибка отправки сообщения пользователю с telegram_id {user_telegram_id}: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю с telegram_id {user_telegram_id}: {e}")
    else:
        logger.warning(f"У пользователя {user.username} нет корректного telegram_id, пропускаем отправку.")

def handle_event_update(event_model, instance):
    if not instance.pk:
        return

    try:
        old_instance = event_model.objects.get(pk=instance.pk)
    except event_model.DoesNotExist:
        return

    # Проверяем, изменилось ли время начала мероприятия
    if old_instance.start_datetime != instance.start_datetime:
        registered_users = Registered.objects.filter(
            online=instance if isinstance(instance, Events_online) else None,
            offline=instance if isinstance(instance, Events_offline) else None,
            attractions=instance if isinstance(instance, Attractions) else None,
            for_visiting=instance if isinstance(instance, Events_for_visiting) else None
        )

        for registration in registered_users:
            send_update_notification(registration.user, instance, instance.start_datetime)

# Обработчик для всех типов событий
@receiver(post_save, sender=Events_online)
@receiver(post_save, sender=Events_offline)
@receiver(post_save, sender=Attractions)
@receiver(post_save, sender=Events_for_visiting)
def handle_event_update_signal(sender, instance, **kwargs):
    handle_event_update(sender, instance)

